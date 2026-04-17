from __future__ import annotations

import csv
import random
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
try:
    import duckdb
except Exception:  # optional fast path dependency
    duckdb = None

try:
    from ..ai.load_predictor import predict_server_load
    from ..ai.predictor import get_or_train_model, predict_execution_time
except ImportError:
    from ai.load_predictor import predict_server_load
    from ai.predictor import get_or_train_model, predict_execution_time

try:
    from .scheduling_engine import allocate_for_schedule, default_servers, schedule_tasks
    from .scheduling_engine import resolve_schedule_type
    from .stage_preprocessing import preprocess_tasks_stage_1_to_3
    from .status import pipeline_status
    from .task_cache import task_cache
    from .tree_structure import build_server_hierarchy, flatten_servers, level_order_server_ids
except ImportError:
    from core.scheduling_engine import allocate_for_schedule, default_servers, schedule_tasks
    from core.scheduling_engine import resolve_schedule_type
    from core.stage_preprocessing import preprocess_tasks_stage_1_to_3
    from core.status import pipeline_status
    from core.task_cache import task_cache
    from core.tree_structure import build_server_hierarchy, flatten_servers, level_order_server_ids


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "cloudmatrix.db"
MODEL_DIR = DATA_DIR / "models"
MODEL_PATH = MODEL_DIR / "execution_time_model.joblib"

REQUIRED_COLUMNS = {"id", "priority", "cpu_request", "memory_request", "execution_time"}
CHUNK_SIZE = 50_000
SUPPORTED_SCHEDULE_TYPES = {"fast", "hybrid", "sjf", "heap", "greedy", "dp", "backtracking", "branch_bound", "graph"}
FAST_DUCKDB_THRESHOLD = 1_000_000
FAST_MAX_TASKS_PER_SERVER = 1000
FAST_RESCHEDULE_THRESHOLD = 100_000


def _connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def initialize_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    with _connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_tasks (
                id TEXT PRIMARY KEY,
                priority REAL,
                cpu_request REAL,
                memory_request REAL,
                execution_time REAL,
                predicted_execution_time REAL,
                priority_score REAL,
                schedule_rank INTEGER,
                scheduling_type TEXT,
                predicted_server_load REAL,
                allocated_server TEXT,
                allocation_success INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_type TEXT,
                total_rows INTEGER,
                completed_rows INTEGER,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_alloc_server ON processed_tasks(allocated_server)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_sched_type ON processed_tasks(scheduling_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_priority ON processed_tasks(priority)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_alloc_success ON processed_tasks(allocation_success)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_sjf ON processed_tasks(predicted_execution_time, priority, id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_rank ON processed_tasks(schedule_rank, id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_processed_tasks_unassigned_priority ON processed_tasks(allocation_success, priority_score DESC)"
        )
        _ensure_table_columns(conn)
        conn.commit()


def _ensure_table_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(processed_tasks)").fetchall()}
    expected = {
        "schedule_rank": "INTEGER",
        "scheduling_type": "TEXT",
        "predicted_server_load": "REAL",
        "allocated_server": "TEXT",
        "allocation_success": "INTEGER",
    }
    for col, col_type in expected.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE processed_tasks ADD COLUMN {col} {col_type}")


def _count_rows(csv_path: Path) -> int:
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.reader(source)
            next(reader, None)
            return sum(1 for _ in reader)
    except Exception:
        total = 0
        for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, usecols=["id"]):
            total += len(chunk)
        return total


def _validate_columns(columns: Iterable[str]) -> None:
    missing = REQUIRED_COLUMNS.difference(set(columns))
    if missing:
        raise ValueError(f"Missing required CSV column(s): {', '.join(sorted(missing))}")


def _to_numeric(chunk: pd.DataFrame) -> pd.DataFrame:
    out = chunk.copy()
    for col in ["priority", "cpu_request", "memory_request", "execution_time"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["id"] = out["id"].astype(str)
    return out


def _compute_priority_score(chunk: pd.DataFrame) -> pd.Series:
    safe_exec = chunk["predicted_execution_time"].astype(float).clip(lower=0.1)
    return (chunk["priority"].astype(float) * 2.0) + (
        (chunk["cpu_request"].astype(float) + chunk["memory_request"].astype(float))
        / safe_exec
    )


def _process_chunk(
    chunk: pd.DataFrame,
    schedule_type: str,
    rank_offset: int,
    model,
    servers: List[Dict],
) -> tuple[pd.DataFrame, List[Dict], int]:
    chunk = _to_numeric(chunk)
    chunk["predicted_execution_time"] = predict_execution_time(chunk, model=model)
    chunk["priority_score"] = _compute_priority_score(chunk)
    chunk["predicted_server_load"] = predict_server_load(chunk)

    # Stage 1-3 preprocessing includes:
    # - hashing for O(1) task-key operations
    # - dependency-aware graph ordering when needed
    # - divide-and-conquer merge sort prioritization
    preprocessed = preprocess_tasks_stage_1_to_3(chunk.to_dict(orient="records"))
    scheduled = schedule_tasks(preprocessed, schedule_type)
    for row in scheduled:
        row["schedule_rank"] = int(row.get("schedule_rank", 0)) + rank_offset

    allocations, unassigned, updated_servers = allocate_for_schedule(
        scheduled,
        schedule_type=schedule_type,
        servers=servers,
    )
    alloc_map = {a["task_id"]: a["server_id"] for a in allocations}
    unassigned_ids = {u["task_id"] for u in unassigned}

    for row in scheduled:
        task_id = str(row.get("id"))
        row["scheduling_type"] = schedule_type
        row["allocated_server"] = alloc_map.get(task_id)
        row["allocation_success"] = 0 if task_id in unassigned_ids else 1

    return pd.DataFrame(scheduled), updated_servers, len(unassigned)


def _persist_chunk(conn: sqlite3.Connection, chunk: pd.DataFrame) -> None:
    rows = [
        (
            str(task_id),
            float(priority),
            float(cpu_request),
            float(memory_request),
            float(execution_time),
            float(predicted_execution_time),
            float(priority_score),
            int(schedule_rank),
            str(scheduling_type or "heap"),
            float(predicted_server_load),
            allocated_server,
            int(allocation_success or 0),
        )
        for (
            task_id,
            priority,
            cpu_request,
            memory_request,
            execution_time,
            predicted_execution_time,
            priority_score,
            schedule_rank,
            scheduling_type,
            predicted_server_load,
            allocated_server,
            allocation_success,
        ) in chunk[
            [
                "id",
                "priority",
                "cpu_request",
                "memory_request",
                "execution_time",
                "predicted_execution_time",
                "priority_score",
                "schedule_rank",
                "scheduling_type",
                "predicted_server_load",
                "allocated_server",
                "allocation_success",
            ]
        ].itertuples(index=False, name=None)
    ]

    conn.executemany(
        """
        INSERT OR REPLACE INTO processed_tasks (
            id, priority, cpu_request, memory_request, execution_time,
            predicted_execution_time, priority_score, schedule_rank, scheduling_type,
            predicted_server_load, allocated_server, allocation_success
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def _persist_batch_rows(conn: sqlite3.Connection, rows: List[tuple]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO processed_tasks (
            id, priority, cpu_request, memory_request, execution_time,
            predicted_execution_time, priority_score, schedule_rank, scheduling_type,
            predicted_server_load, allocated_server, allocation_success
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _rank_order_sql(schedule_type: str) -> str:
    """
    SQL ORDER BY clause equivalent for scheduler ranking.
    """
    if schedule_type == "sjf":
        return """
        COALESCE(predicted_execution_time, execution_time, 0.0) ASC,
        COALESCE(priority, 0.0) DESC,
        id ASC
        """
    if schedule_type in {"heap", "branch_bound", "backtracking", "graph"}:
        return """
        COALESCE(priority_score, priority, 0.0) DESC,
        COALESCE(priority, 0.0) DESC,
        id ASC
        """
    if schedule_type in {"greedy", "dp"}:
        return """
        COALESCE(priority_score, priority, 0.0) DESC,
        id ASC
        """
    # Safe fallback: priority-first ordering.
    return """
    COALESCE(priority_score, priority, 0.0) DESC,
    COALESCE(priority, 0.0) DESC,
    id ASC
    """


def _reschedule_via_sql(conn: sqlite3.Connection, schedule_type: str, total: int) -> Dict:
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute(
        f"""
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    ORDER BY {_rank_order_sql(schedule_type)}
                ) AS rn
            FROM processed_tasks
        )
        UPDATE processed_tasks
        SET schedule_rank = (
                SELECT rn FROM ranked WHERE ranked.id = processed_tasks.id
            ),
            scheduling_type = ?
        """,
        (schedule_type,),
    )
    total_unassigned = conn.execute(
        "SELECT COUNT(*) FROM processed_tasks WHERE allocation_success = 0"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
        (schedule_type, total, total, "completed"),
    )
    conn.commit()
    return {
        "rescheduled": int(total),
        "schedule_type": schedule_type,
        "unassigned": int(total_unassigned),
        "fast_path": "sql",
    }


def _run_pipeline_duckdb_fast(
    csv_path: Path,
    requested_schedule: str,
    initial_server_count: int,
    total_rows: int,
) -> None:
    effective_schedule = resolve_schedule_type(requested_schedule, total_rows)
    server_count = max(1, int(initial_server_count or 1))
    pipeline_status.update(
        message=f"Pipeline started using fast-duckdb ({effective_schedule}) with {server_count} servers",
        total_rows=total_rows,
        server_count=server_count,
    )

    if duckdb is None:
        raise RuntimeError("duckdb is not installed for fast processing mode")

    order_sql = (
        "predicted_execution_time ASC, priority DESC, id ASC"
        if effective_schedule == "sjf"
        else "priority_score DESC, abs(hash(id)) ASC"
    )

    conn = _connect_db()
    dcon = duckdb.connect(database=":memory:")
    try:
        conn.execute("DELETE FROM processed_tasks")
        conn.execute(
            "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
            (effective_schedule, total_rows, 0, "processing"),
        )
        conn.commit()

        csv_literal = str(csv_path).replace("\\", "\\\\").replace("'", "''")
        dcon.execute(
            f"""
            CREATE VIEW raw_tasks AS
            SELECT * FROM read_csv_auto('{csv_literal}', header=true, sample_size=-1);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        col_names = {str(item[0]) for item in dcon.execute("DESCRIBE raw_tasks").fetchall()}
        missing = REQUIRED_COLUMNS.difference(col_names)
        if missing:
            raise ValueError(f"Missing required CSV column(s): {', '.join(sorted(missing))}")

        dcon.execute(
            f"""
            CREATE TABLE final_rows AS
            WITH normalized AS (
                SELECT
                    CAST(id AS VARCHAR) AS id,
                    COALESCE(TRY_CAST(priority AS DOUBLE), 0.0) AS priority,
                    COALESCE(TRY_CAST(cpu_request AS DOUBLE), 0.0) AS cpu_request,
                    COALESCE(TRY_CAST(memory_request AS DOUBLE), 0.0) AS memory_request,
                    COALESCE(TRY_CAST(execution_time AS DOUBLE), 0.0) AS execution_time
                FROM raw_tasks
            ),
            scored AS (
                SELECT
                    id, priority, cpu_request, memory_request, execution_time,
                    execution_time AS predicted_execution_time,
                    (priority * 2.0) + ((cpu_request + memory_request) / GREATEST(execution_time, 0.1)) AS priority_score,
                    ((cpu_request + memory_request) / GREATEST(execution_time, 0.1)) AS predicted_server_load
                FROM normalized
            ),
            ranked AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (ORDER BY {order_sql}) AS schedule_rank,
                    ROW_NUMBER() OVER (ORDER BY predicted_server_load DESC, abs(hash(id)) ASC) AS rr
                FROM scored
            )
            SELECT
                id,
                priority,
                cpu_request,
                memory_request,
                execution_time,
                predicted_execution_time,
                priority_score,
                schedule_rank,
                '{effective_schedule}' AS scheduling_type,
                predicted_server_load,
                CONCAT('S', CAST(1 + MOD(rr - 1, {int(server_count)}) AS VARCHAR)) AS allocated_server,
                1 AS allocation_success
            FROM ranked
            """
        )

        cursor = dcon.execute(
            """
            SELECT
                id, priority, cpu_request, memory_request, execution_time,
                predicted_execution_time, priority_score, schedule_rank, scheduling_type,
                predicted_server_load, allocated_server, allocation_success
            FROM final_rows
            ORDER BY schedule_rank ASC
            """
        )

        processed = 0
        batch_size = 50_000
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            _persist_batch_rows(conn, rows)
            processed += len(rows)
            progress = min(100, int((processed / max(total_rows, 1)) * 100))
            conn.execute(
                """
                UPDATE pipeline_runs
                SET completed_rows = ?, status = ?
                WHERE run_id = (SELECT MAX(run_id) FROM pipeline_runs)
                """,
                (processed, "processing"),
            )
            conn.commit()
            pipeline_status.update(
                status="processing",
                progress=progress,
                rows_processed=processed,
                message=f"Processed {processed}/{total_rows} rows (fast-duckdb {effective_schedule})",
            )

        conn.execute(
            """
            UPDATE pipeline_runs
            SET completed_rows = ?, status = ?
            WHERE run_id = (SELECT MAX(run_id) FROM pipeline_runs)
            """,
            (processed, "completed"),
        )
        conn.commit()

        pipeline_status.update(
            status="completed",
            progress=100,
            rows_processed=processed,
            total_rows=total_rows,
            message=f"Pipeline completed (fast-duckdb {effective_schedule}). Unassigned tasks: 0",
            error=None,
        )
    finally:
        try:
            dcon.close()
        except Exception:
            pass
        conn.close()


def run_pipeline(csv_path: Path, schedule_type: str = "heap", initial_unused_servers: int = 3) -> None:
    initialize_storage()
    task_cache.clear()

    schedule_type = schedule_type.lower()
    if schedule_type not in SUPPORTED_SCHEDULE_TYPES:
        schedule_type = "fast"

    pipeline_status.reset()
    server_count = max(1, int(initial_unused_servers or 1))
    _store_configured_server_count(server_count)
    pipeline_status.update(message=f"Pipeline started using {schedule_type}", server_count=server_count)

    try:
        total_rows = _count_rows(csv_path)
        if total_rows >= FAST_DUCKDB_THRESHOLD and duckdb is not None:
            _run_pipeline_duckdb_fast(
                csv_path=csv_path,
                requested_schedule=schedule_type,
                initial_server_count=server_count,
                total_rows=total_rows,
            )
            return

        effective_schedule = resolve_schedule_type(schedule_type, total_rows)
        pipeline_status.update(total_rows=total_rows)

        if total_rows == 0:
            pipeline_status.update(status="failed", progress=0, message="Uploaded CSV is empty", error="No rows found")
            return

        with _connect_db() as conn:
            conn.execute("DELETE FROM processed_tasks")
            conn.execute(
                "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
                (effective_schedule, total_rows, 0, "processing"),
            )
            conn.commit()

            model = None
            first_chunk = True
            processed = 0
            total_unassigned = 0
            servers = default_servers(server_count)

            for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE):
                if first_chunk:
                    _validate_columns(chunk.columns)
                    model = get_or_train_model(training_df=chunk, model_path=MODEL_PATH, algorithm="linear")
                    first_chunk = False

                processed_chunk, servers, unassigned_count = _process_chunk(
                    chunk=chunk,
                    schedule_type=effective_schedule,
                    rank_offset=processed,
                    model=model,
                    servers=servers,
                )
                _persist_chunk(conn, processed_chunk)

                processed += len(processed_chunk)
                total_unassigned += unassigned_count
                progress = min(100, int((processed / total_rows) * 100))

                conn.execute(
                    """
                    UPDATE pipeline_runs
                    SET completed_rows = ?, status = ?
                    WHERE run_id = (SELECT MAX(run_id) FROM pipeline_runs)
                    """,
                    (processed, "processing"),
                )
                conn.commit()

                pipeline_status.update(
                    status="processing",
                    progress=progress,
                    rows_processed=processed,
                    message=f"Processed {processed}/{total_rows} rows ({effective_schedule})",
                )

            conn.execute(
                """
                UPDATE pipeline_runs
                SET completed_rows = ?, status = ?
                WHERE run_id = (SELECT MAX(run_id) FROM pipeline_runs)
                """,
                (processed, "completed"),
            )
            conn.commit()

        pipeline_status.update(
            status="completed",
            progress=100,
            rows_processed=total_rows,
            message=f"Pipeline completed ({effective_schedule}). Unassigned tasks: {total_unassigned}",
            error=None,
        )
    except Exception as exc:
        pipeline_status.update(status="failed", message="Pipeline failed", error=str(exc))


def _configured_server_count() -> int:
    snapshot = pipeline_status.snapshot()
    runtime = int(snapshot.get("server_count") or 0)
    if runtime > 0:
        return max(1, runtime)
    return max(1, _read_configured_server_count(default=3))


def get_configured_server_count() -> int:
    return _configured_server_count()


def _store_configured_server_count(server_count: int) -> None:
    initialize_storage()
    with _connect_db() as conn:
        conn.execute(
            """
            INSERT INTO app_config(key, value)
            VALUES('server_count', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (str(max(1, int(server_count or 1))),),
        )
        conn.commit()


def _read_configured_server_count(default: int = 3) -> int:
    initialize_storage()
    try:
        with _connect_db() as conn:
            row = conn.execute("SELECT value FROM app_config WHERE key = 'server_count'").fetchone()
            if not row:
                return int(default)
            return max(1, int(str(row[0] or default)))
    except Exception:
        return int(default)


def reschedule_existing_tasks(schedule_type: str) -> Dict:
    initialize_storage()
    task_cache.clear()

    schedule_type = schedule_type.lower()
    if schedule_type not in SUPPORTED_SCHEDULE_TYPES:
        raise ValueError(f"Unsupported schedule type: {schedule_type}")

    with _connect_db() as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) FROM processed_tasks").fetchone()[0]

        if total == 0:
            return {"rescheduled": 0, "schedule_type": schedule_type}

        effective_schedule = resolve_schedule_type(schedule_type, total)

        equivalent_types = {effective_schedule}
        if total >= FAST_RESCHEDULE_THRESHOLD and effective_schedule in {"heap", "greedy"}:
            # For very large datasets, these two orderings are both treated as fast-priority modes.
            # Skipping cross-rewrites avoids expensive full-table updates.
            equivalent_types.update({"heap", "greedy"})

        placeholders = ",".join("?" for _ in equivalent_types)
        already_current = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM processed_tasks
            WHERE COALESCE(scheduling_type, '') NOT IN ({placeholders})
            """,
            tuple(sorted(equivalent_types)),
        ).fetchone()[0]
        if int(already_current or 0) == 0:
            total_unassigned = conn.execute(
                "SELECT COUNT(*) FROM processed_tasks WHERE allocation_success = 0"
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
                (effective_schedule, total, total, "completed"),
            )
            conn.commit()
            return {
                "rescheduled": int(total),
                "schedule_type": effective_schedule,
                "unassigned": int(total_unassigned),
                "skipped": True,
            }

        # Fast path for large datasets and SQL-friendly orderings.
        # Avoids expensive OFFSET scans and per-row update loops.
        if total >= FAST_RESCHEDULE_THRESHOLD and effective_schedule in {
            "sjf",
            "heap",
            "greedy",
            "branch_bound",
            "backtracking",
            "graph",
            "dp",
        }:
            return _reschedule_via_sql(conn, effective_schedule, total)

        # Existing SJF SQL path for small-medium datasets.
        if effective_schedule == "sjf":
            already_sjf = conn.execute(
                """
                SELECT COUNT(*)
                FROM processed_tasks
                WHERE COALESCE(scheduling_type, '') <> 'sjf'
                """
            ).fetchone()[0]
            if int(already_sjf or 0) == 0:
                total_unassigned = conn.execute(
                    "SELECT COUNT(*) FROM processed_tasks WHERE allocation_success = 0"
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
                    (effective_schedule, total, total, "completed"),
                )
                conn.commit()
                return {
                    "rescheduled": int(total),
                    "schedule_type": effective_schedule,
                    "unassigned": int(total_unassigned),
                    "skipped": True,
                }
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute(
                """
                WITH ranked AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            ORDER BY
                                COALESCE(predicted_execution_time, execution_time, 0.0) ASC,
                                COALESCE(priority, 0.0) DESC,
                                id ASC
                        ) AS rn
                    FROM processed_tasks
                )
                UPDATE processed_tasks
                SET schedule_rank = (
                        SELECT rn FROM ranked WHERE ranked.id = processed_tasks.id
                    ),
                    scheduling_type = ?
                """,
                (effective_schedule,),
            )
            total_unassigned = conn.execute(
                "SELECT COUNT(*) FROM processed_tasks WHERE allocation_success = 0"
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
                (effective_schedule, total, total, "completed"),
            )
            conn.commit()
            return {
                "rescheduled": int(total),
                "schedule_type": effective_schedule,
                "unassigned": int(total_unassigned),
            }
        servers = default_servers(_configured_server_count())
        offset = 0
        global_rank = 0
        total_unassigned = 0

        while True:
            rows = conn.execute(
                """
                SELECT id, priority, cpu_request, memory_request, execution_time,
                       predicted_execution_time, priority_score, predicted_server_load
                FROM processed_tasks
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (CHUNK_SIZE, offset),
            ).fetchall()

            if not rows:
                break

            tasks = [dict(r) for r in rows]
            scheduled = schedule_tasks(tasks, effective_schedule)
            for row in scheduled:
                row["schedule_rank"] = int(row.get("schedule_rank", 0)) + global_rank

            allocations, unassigned, servers = allocate_for_schedule(
                scheduled,
                schedule_type=effective_schedule,
                servers=servers,
            )
            alloc_map = {a["task_id"]: a["server_id"] for a in allocations}
            unassigned_ids = {u["task_id"] for u in unassigned}
            total_unassigned += len(unassigned_ids)

            updates = []
            for row in scheduled:
                task_id = str(row["id"])
                updates.append(
                    (
                        int(row["schedule_rank"]),
                        effective_schedule,
                        alloc_map.get(task_id),
                        0 if task_id in unassigned_ids else 1,
                        task_id,
                    )
                )

            conn.executemany(
                """
                UPDATE processed_tasks
                SET schedule_rank = ?, scheduling_type = ?,
                    allocated_server = ?, allocation_success = ?
                WHERE id = ?
                """,
                updates,
            )
            conn.commit()

            global_rank += len(scheduled)
            offset += CHUNK_SIZE

        conn.execute(
            "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
            (effective_schedule, total, total, "completed"),
        )
        conn.commit()

    return {
        "rescheduled": int(total),
        "schedule_type": effective_schedule,
        "unassigned": int(total_unassigned),
    }


def _load_ratio(server: Dict) -> float:
    cpu_cap = float(server["cpu_capacity"])
    mem_cap = float(server["memory_capacity"])
    cpu_used = cpu_cap - float(server["cpu_available"])
    mem_used = mem_cap - float(server["memory_available"])
    cpu_ratio = (cpu_used / cpu_cap) if cpu_cap else 1.0
    mem_ratio = (mem_used / mem_cap) if mem_cap else 1.0
    return (cpu_ratio + mem_ratio) / 2


def _pick_random_balanced_server(candidates: List[Dict], cpu_req: float, mem_req: float) -> Dict:
    ranked = sorted(candidates, key=_load_ratio)
    window = ranked[: max(1, min(4, len(ranked)))]
    weights = []
    for server in window:
        cpu_cap = float(server["cpu_capacity"])
        mem_cap = float(server["memory_capacity"])
        cpu_slack = ((float(server["cpu_available"]) - cpu_req) / cpu_cap) if cpu_cap else 0.0
        mem_slack = ((float(server["memory_available"]) - mem_req) / mem_cap) if mem_cap else 0.0
        weight = max(0.05, 1.0 - _load_ratio(server) + max(0.0, cpu_slack) + max(0.0, mem_slack))
        weights.append(weight)
    return random.choices(window, weights=weights, k=1)[0]


def _build_server_pool_from_db(conn: sqlite3.Connection, configured_count: int) -> List[Dict]:
    defaults = {s["server_id"]: dict(s) for s in default_servers(configured_count)}
    usage_rows = conn.execute(
        """
        SELECT allocated_server, COALESCE(SUM(cpu_request), 0), COALESCE(SUM(memory_request), 0)
        FROM processed_tasks
        WHERE allocation_success = 1
          AND allocated_server GLOB 'S[0-9]*'
          AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
        GROUP BY allocated_server
        """
    , (int(configured_count),)).fetchall()

    pool: List[Dict] = []
    seen = set()
    for server_id, cpu_used, mem_used in usage_rows:
        sid = str(server_id)
        cpu_used = float(cpu_used or 0.0)
        mem_used = float(mem_used or 0.0)

        if sid in defaults:
            base = defaults[sid]
            cpu_cap = float(base["cpu_capacity"])
            mem_cap = float(base["memory_capacity"])
        else:
            # Ignore legacy AUTO_* pools and cap to configured server set.
            continue

        pool.append(
            {
                "server_id": sid,
                "cpu_capacity": cpu_cap,
                "memory_capacity": mem_cap,
                "cpu_available": max(0.0, cpu_cap - cpu_used),
                "memory_available": max(0.0, mem_cap - mem_used),
            }
        )
        seen.add(sid)

    for sid, server in defaults.items():
        if sid not in seen:
            pool.append(dict(server))

    return pool


def rebalance_unassigned_tasks(
    auto_scale: bool = True,
    max_rows: int = 200_000,
    batch_size: int = 25_000,
) -> Dict:
    initialize_storage()
    task_cache.clear()

    configured_count = _configured_server_count()
    with _connect_db() as conn:
        total_unassigned = conn.execute(
            """
            SELECT COUNT(*)
            FROM processed_tasks
            WHERE NOT (
                allocation_success = 1
                AND allocated_server GLOB 'S[0-9]*'
                AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
            )
            """,
            (int(configured_count),),
        ).fetchone()[0]
        if total_unassigned == 0:
            return {
                "message": "No unassigned tasks found",
                "rebalanced": 0,
                "remaining_unassigned": 0,
                "new_servers": 0,
                "partial": False,
            }

        servers = _build_server_pool_from_db(conn, configured_count)
        new_servers = 0
        updates: List[tuple] = []
        assigned_now = 0
        scanned_rows = 0

        while True:
            if scanned_rows >= max_rows:
                break

            fetch_size = min(batch_size, max_rows - scanned_rows)
            rows = conn.execute(
                """
                SELECT id, cpu_request, memory_request
                FROM processed_tasks
                WHERE NOT (
                    allocation_success = 1
                    AND allocated_server GLOB 'S[0-9]*'
                    AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
                )
                ORDER BY priority_score DESC
                LIMIT ?
                """,
                (int(configured_count), fetch_size),
            ).fetchall()
            if not rows:
                break
            scanned_rows += len(rows)

            for task_id, cpu_req, mem_req in rows:
                cpu_req = float(cpu_req or 0.0)
                mem_req = float(mem_req or 0.0)

                candidates = [
                    s
                    for s in servers
                    if s["cpu_available"] >= cpu_req and s["memory_available"] >= mem_req
                ]
                if not candidates:
                    continue

                best = _pick_random_balanced_server(candidates, cpu_req, mem_req)
                best["cpu_available"] -= cpu_req
                best["memory_available"] -= mem_req
                updates.append((best["server_id"], 1, str(task_id)))
                assigned_now += 1

            if updates:
                conn.executemany(
                    """
                    UPDATE processed_tasks
                    SET allocated_server = ?, allocation_success = ?
                    WHERE id = ?
                    """,
                    updates,
                )
                conn.commit()
                updates.clear()
            else:
                # No progress in this batch.
                break

        remaining = conn.execute(
            """
            SELECT COUNT(*)
            FROM processed_tasks
            WHERE NOT (
                allocation_success = 1
                AND allocated_server GLOB 'S[0-9]*'
                AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
            )
            """,
            (int(configured_count),),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO pipeline_runs (schedule_type, total_rows, completed_rows, status) VALUES (?, ?, ?, ?)",
            ("rebalance", total_unassigned, assigned_now, "completed"),
        )
        conn.commit()

    return {
        "message": "Rebalance batch completed",
        "rebalanced": int(assigned_now),
        "remaining_unassigned": int(remaining),
        "new_servers": int(new_servers),
        "processed_rows": int(scanned_rows),
        "partial": bool(remaining > 0),
    }


def get_server_balance() -> Dict:
    initialize_storage()
    configured_count = _configured_server_count()
    with _connect_db() as conn:
        rows = conn.execute(
            """
            SELECT
                CASE
                    WHEN allocated_server GLOB 'S[0-9]*'
                         AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
                    THEN allocated_server
                    ELSE 'unassigned'
                END as server_id,
                COUNT(*) as task_count,
                COALESCE(SUM(cpu_request), 0) as cpu_used,
                COALESCE(SUM(memory_request), 0) as memory_used,
                COALESCE(AVG(predicted_server_load), 0) as avg_predicted_load
            FROM processed_tasks
            GROUP BY
                CASE
                    WHEN allocated_server GLOB 'S[0-9]*'
                         AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
                    THEN allocated_server
                    ELSE 'unassigned'
                END
            ORDER BY task_count DESC
            """
        , (int(configured_count), int(configured_count))).fetchall()
        unassigned = conn.execute(
            """
            SELECT COUNT(*)
            FROM processed_tasks
            WHERE NOT (
                allocation_success = 1
                AND allocated_server GLOB 'S[0-9]*'
                AND CAST(SUBSTR(allocated_server, 2) AS INTEGER) BETWEEN 1 AND ?
            )
            """,
            (int(configured_count),),
        ).fetchone()[0]

    defaults = {s["server_id"]: s for s in default_servers(_configured_server_count())}
    servers = []
    for server_id, task_count, cpu_used, memory_used, avg_load in rows:
        sid = str(server_id)
        cpu_used = float(cpu_used or 0.0)
        memory_used = float(memory_used or 0.0)
        if sid in defaults:
            cpu_cap = float(defaults[sid]["cpu_capacity"])
            mem_cap = float(defaults[sid]["memory_capacity"])
        elif sid == "unassigned":
            cpu_cap = 0.0
            mem_cap = 0.0
        else:
            # Keep reporting fixed to provided server set only.
            continue

        cpu_util = (cpu_used / cpu_cap * 100.0) if cpu_cap else 0.0
        mem_util = (memory_used / mem_cap * 100.0) if mem_cap else 0.0
        servers.append(
            {
                "server_id": sid,
                "task_count": int(task_count),
                "cpu_used": cpu_used,
                "memory_used": memory_used,
                "cpu_capacity": cpu_cap,
                "memory_capacity": mem_cap,
                "cpu_available": max(0.0, cpu_cap - cpu_used),
                "memory_available": max(0.0, mem_cap - memory_used),
                "cpu_utilization_pct": round(cpu_util, 2),
                "memory_utilization_pct": round(mem_util, 2),
                "avg_predicted_load": round(float(avg_load or 0.0), 4),
            }
        )

    # Basic tree concepts used in runtime response:
    # - hierarchy construction
    # - breadth-first traversal (level order)
    hierarchy = build_server_hierarchy(servers)
    tree_nodes = flatten_servers(hierarchy)
    level_order = level_order_server_ids(hierarchy)

    return {
        "servers": servers,
        "remaining_unassigned": int(unassigned),
        "server_tree": {
            "root": hierarchy.server_id,
            "level_order": level_order,
            "nodes": tree_nodes,
        },
    }
