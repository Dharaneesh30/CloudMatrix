from __future__ import annotations

from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile

try:
    from ..core.pipeline import (
        DB_PATH,
        SUPPORTED_SCHEDULE_TYPES,
        UPLOAD_DIR,
        get_server_balance,
        initialize_storage,
        rebalance_unassigned_tasks,
        reschedule_existing_tasks,
        run_pipeline,
    )
    from ..core.status import pipeline_status
    from ..core.task_cache import task_cache
except ImportError:
    from core.pipeline import (
        DB_PATH,
        SUPPORTED_SCHEDULE_TYPES,
        UPLOAD_DIR,
        get_server_balance,
        initialize_storage,
        rebalance_unassigned_tasks,
        reschedule_existing_tasks,
        run_pipeline,
    )
    from core.status import pipeline_status
    from core.task_cache import task_cache


router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "cloudmatrix-fastapi"}


@router.post("/upload-dataset")
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    unused_servers: int = Form(default=3),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    if unused_servers < 1 or unused_servers > 500:
        raise HTTPException(status_code=400, detail="unused_servers must be between 1 and 500")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}_{Path(file.filename).name}"
    target_path = UPLOAD_DIR / safe_name

    try:
        with target_path.open("wb") as destination:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                destination.write(chunk)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc
    finally:
        await file.close()

    pipeline_status.update(
        status="queued",
        progress=0,
        rows_processed=0,
        total_rows=0,
        message=f"Dataset uploaded. Automatic pipeline queued with {unused_servers} servers",
        error=None,
        server_count=int(unused_servers),
    )
    # Stage selection is internal-only; users trigger one automated pipeline.
    background_tasks.add_task(run_pipeline, target_path, "fast", int(unused_servers))

    return {
        "message": "Dataset uploaded and pipeline started",
        "filename": file.filename,
        "saved_as": safe_name,
        "processing_mode": "auto",
        "unused_servers": int(unused_servers),
    }


@router.get("/status")
async def get_status() -> dict:
    snapshot = pipeline_status.snapshot()

    # Recover UI state after backend restarts by inferring last known run from SQLite.
    # Without this, pages gated by `hasRun` stay locked even when processed data exists.
    if int(snapshot.get("rows_processed", 0) or 0) > 0 or int(snapshot.get("total_rows", 0) or 0) > 0:
        return snapshot

    try:
        initialize_storage()
        with sqlite3.connect(DB_PATH, timeout=8) as conn:
            total_tasks = int(conn.execute("SELECT COUNT(*) FROM processed_tasks").fetchone()[0] or 0)
            recent = conn.execute(
                """
                SELECT status, total_rows, completed_rows, schedule_type, created_at
                FROM pipeline_runs
                ORDER BY run_id DESC
                LIMIT 1
                """
            ).fetchone()
    except sqlite3.DatabaseError:
        return snapshot

    if total_tasks <= 0:
        return snapshot

    if recent:
        run_status = str(recent[0] or "completed").lower()
        total_rows = int(recent[1] or total_tasks)
        completed_rows = int(recent[2] or total_tasks)
        schedule_type = str(recent[3] or "unknown")
        created_at = str(recent[4] or "")
        phase = "completed" if run_status in {"completed", "success"} else run_status
        message = f"Recovered last run ({schedule_type}) from {created_at}".strip()
    else:
        phase = "completed"
        total_rows = total_tasks
        completed_rows = total_tasks
        message = "Recovered processed dataset from storage"

    recovered = {
        **snapshot,
        "status": phase,
        "progress": 100 if total_rows > 0 and completed_rows >= total_rows else int((completed_rows / max(total_rows, 1)) * 100),
        "rows_processed": completed_rows,
        "total_rows": total_rows,
        "message": message,
        "error": None,
    }
    pipeline_status.update(**recovered)
    return recovered


@router.get("/tasks")
async def get_tasks(page: int = 1, limit: int = 50) -> dict:
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")

    initialize_storage()
    offset = (page - 1) * limit

    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) FROM processed_tasks").fetchone()[0]
        rows = conn.execute(
            """
            SELECT id, priority, cpu_request, memory_request, execution_time,
                   predicted_execution_time, priority_score, schedule_rank, scheduling_type,
                   predicted_server_load, allocated_server, allocation_success
            FROM processed_tasks
            ORDER BY schedule_rank ASC, id ASC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    status = pipeline_status.snapshot()
    rows_processed = int(status.get("rows_processed", 0) or 0)
    phase = str(status.get("status") or "idle")
    tasks = []
    for row in rows:
        payload = dict(row)
        rank = int(payload.get("schedule_rank") or 0)
        allocated = int(payload.get("allocation_success") or 0) == 1
        if phase in {"queued", "processing"} and rank > rows_processed:
            payload["task_status"] = "queued"
        elif allocated:
            payload["task_status"] = "completed"
        else:
            payload["task_status"] = "unassigned"
        tasks.append(payload)

    return {
        "page": page,
        "limit": limit,
        "total": int(total),
        "tasks": tasks,
    }


@router.get("/unassigned-tasks")
async def get_unassigned_tasks(
    page: int = 1,
    limit: int = 50,
    include_total: bool = Query(default=False),
) -> dict:
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")

    initialize_storage()
    offset = (page - 1) * limit
    last_exc = None

    for _ in range(5):
        try:
            with sqlite3.connect(DB_PATH, timeout=15) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=8000")
                conn.execute("PRAGMA query_only=1")
                conn.row_factory = sqlite3.Row
                total = None
                if include_total:
                    total = conn.execute(
                        "SELECT COUNT(*) FROM processed_tasks WHERE allocation_success = 0"
                    ).fetchone()[0]
                rows = conn.execute(
                    """
                    SELECT id, priority, cpu_request, memory_request, execution_time,
                           predicted_execution_time, priority_score, schedule_rank, scheduling_type,
                           predicted_server_load, allocated_server, allocation_success
                    FROM processed_tasks
                    WHERE allocation_success = 0
                    ORDER BY priority_score DESC, id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (limit + 1, offset),
                ).fetchall()
                has_more = len(rows) > limit
                rows = rows[:limit]

            return {
                "page": page,
                "limit": limit,
                "total": int(total) if total is not None else None,
                "has_more": bool(has_more),
                "tasks": [{**dict(row), "task_status": "unassigned"} for row in rows],
                "degraded": False,
            }
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
            last_exc = exc
            time.sleep(0.35)

    return {
        "page": page,
        "limit": limit,
        "total": 0 if include_total else None,
        "has_more": False,
        "tasks": [],
        "degraded": True,
        "degraded_reason": str(last_exc) if last_exc else "temporary_unassigned_unavailable",
    }


@router.get("/task/{task_id}")
async def get_task(task_id: str) -> dict:
    initialize_storage()
    status = pipeline_status.snapshot()
    phase = str(status.get("status") or "idle")

    cached = task_cache.get(task_id)
    if cached is not None:
        cached_allocated = int(cached.get("allocation_success") or 0) == 1 or bool(cached.get("allocated_server"))
        # Avoid stale "not allocated" responses:
        # if a task was cached earlier as unassigned, re-read from DB on lookup.
        if cached_allocated:
            return cached

    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, priority, cpu_request, memory_request, execution_time,
                   predicted_execution_time, priority_score, schedule_rank, scheduling_type,
                   predicted_server_load, allocated_server, allocation_success
            FROM processed_tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    payload = dict(row)
    rows_processed = int(status.get("rows_processed", 0) or 0)
    rank = int(payload.get("schedule_rank") or 0)
    allocated = int(payload.get("allocation_success") or 0) == 1 or bool(payload.get("allocated_server"))
    payload["allocation_success"] = 1 if allocated else 0
    if phase in {"queued", "processing"} and rank > rows_processed:
        payload["task_status"] = "queued"
    elif allocated:
        payload["task_status"] = "completed"
    else:
        payload["task_status"] = "unassigned"
    payload["allocated"] = "yes" if allocated else "no"
    task_cache.put(task_id, payload)
    return payload


@router.post("/schedule/{schedule_type}")
async def schedule_tasks_endpoint(
    schedule_type: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    schedule_type = schedule_type.lower().strip()
    if schedule_type not in SUPPORTED_SCHEDULE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported schedule_type. Use one of: {sorted(SUPPORTED_SCHEDULE_TYPES)}",
        )

    try:
        outcome = reschedule_existing_tasks(schedule_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    paged = await get_tasks(page=page, limit=limit)
    return {
        "message": "Scheduling updated",
        "result": outcome,
        "page": paged,
    }


def _quick_processing_metrics(status: dict) -> dict:
    """
    Fast non-blocking metrics payload for heavy ingestion windows.
    Avoids large aggregate scans while pipeline writes are active.
    """
    processed = int(status.get("rows_processed", 0) or 0)
    return {
        "total_tasks": processed,
        "avg_execution_time": 0.0,
        "avg_predicted_execution_time": 0.0,
        "avg_priority": 0.0,
        "avg_predicted_server_load": 0.0,
        "active_servers": 0,
        "priority_distribution": [],
        "server_load_distribution": [],
        "schedule_mix": [],
        "status": status,
        "recent_run": None,
        "degraded": True,
        "degraded_reason": "processing_snapshot",
    }


def _lite_metrics_from_db(status: dict) -> dict:
    last_exc = None
    for _ in range(2):
        try:
            with sqlite3.connect(DB_PATH, timeout=8) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=3000")
                conn.execute("PRAGMA query_only=1")
                total = conn.execute("SELECT COUNT(*) FROM processed_tasks").fetchone()[0]
                avg_exec = conn.execute("SELECT COALESCE(AVG(execution_time), 0) FROM processed_tasks").fetchone()[0]
                avg_pred = conn.execute("SELECT COALESCE(AVG(predicted_execution_time), 0) FROM processed_tasks").fetchone()[0]
                avg_priority = conn.execute("SELECT COALESCE(AVG(priority), 0) FROM processed_tasks").fetchone()[0]
                avg_load = conn.execute("SELECT COALESCE(AVG(predicted_server_load), 0) FROM processed_tasks").fetchone()[0]
                active_servers = conn.execute(
                    """
                    SELECT COUNT(DISTINCT allocated_server)
                    FROM processed_tasks
                    WHERE allocated_server IS NOT NULL
                    """
                ).fetchone()[0]
                recent_run = conn.execute(
                    """
                    SELECT schedule_type, total_rows, completed_rows, status, created_at
                    FROM pipeline_runs
                    ORDER BY run_id DESC
                    LIMIT 1
                    """
                ).fetchone()

            return {
                "total_tasks": int(total),
                "avg_execution_time": float(avg_exec),
                "avg_predicted_execution_time": float(avg_pred),
                "avg_priority": float(avg_priority),
                "avg_predicted_server_load": float(avg_load),
                "active_servers": int(active_servers),
                "priority_distribution": [],
                "server_load_distribution": [],
                "schedule_mix": [],
                "status": status,
                "recent_run": (
                    {
                        "schedule_type": recent_run[0],
                        "total_rows": recent_run[1],
                        "completed_rows": recent_run[2],
                        "status": recent_run[3],
                        "created_at": recent_run[4],
                    }
                    if recent_run
                    else None
                ),
                "degraded": False,
                "mode": "lite",
            }
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
            last_exc = exc
            time.sleep(0.35)

    return {
        "total_tasks": int(status.get("rows_processed", 0) or 0),
        "avg_execution_time": 0.0,
        "avg_predicted_execution_time": 0.0,
        "avg_priority": 0.0,
        "avg_predicted_server_load": 0.0,
        "active_servers": 0,
        "priority_distribution": [],
        "server_load_distribution": [],
        "schedule_mix": [],
        "status": status,
        "recent_run": None,
        "degraded": True,
        "degraded_reason": str(last_exc) if last_exc else "temporary_metrics_unavailable",
        "mode": "lite",
    }


@router.get("/metrics")
async def get_metrics(mode: str = Query(default="auto")) -> dict:
    initialize_storage()
    status = pipeline_status.snapshot()
    normalized_mode = (mode or "auto").strip().lower()

    if normalized_mode not in {"auto", "full", "lite"}:
        raise HTTPException(status_code=400, detail="mode must be one of: auto, full, lite")

    # During active ingestion, return an immediate snapshot by default.
    if normalized_mode in {"auto", "lite"} and status.get("status") in {"queued", "processing"}:
        return _quick_processing_metrics(status)
    if normalized_mode == "lite":
        return _lite_metrics_from_db(status)

    # During heavy pipeline writes, SQLite may temporarily lock.
    # Retry briefly, then return a degraded but valid response.
    last_exc = None
    for _ in range(2):
        try:
            with sqlite3.connect(DB_PATH, timeout=8) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=3000")
                conn.execute("PRAGMA query_only=1")
                total = conn.execute("SELECT COUNT(*) FROM processed_tasks").fetchone()[0]
                avg_exec = conn.execute("SELECT COALESCE(AVG(execution_time), 0) FROM processed_tasks").fetchone()[0]
                avg_pred = conn.execute("SELECT COALESCE(AVG(predicted_execution_time), 0) FROM processed_tasks").fetchone()[0]
                avg_priority = conn.execute("SELECT COALESCE(AVG(priority), 0) FROM processed_tasks").fetchone()[0]
                avg_load = conn.execute("SELECT COALESCE(AVG(predicted_server_load), 0) FROM processed_tasks").fetchone()[0]
                active_servers = conn.execute(
                    """
                    SELECT COUNT(DISTINCT allocated_server)
                    FROM processed_tasks
                    WHERE allocated_server IS NOT NULL
                    """
                ).fetchone()[0]

                priority_distribution = conn.execute(
                    """
                    SELECT
                        CASE
                            WHEN priority >= 8 THEN 'high'
                            WHEN priority >= 4 THEN 'medium'
                            ELSE 'low'
                        END AS band,
                        COUNT(*) as count
                    FROM processed_tasks
                    GROUP BY band
                    ORDER BY count DESC
                    """
                ).fetchall()

                server_load_distribution = conn.execute(
                    """
                    SELECT COALESCE(allocated_server, 'unassigned') as server, COUNT(*) as count
                    FROM processed_tasks
                    GROUP BY COALESCE(allocated_server, 'unassigned')
                    ORDER BY count DESC
                    """
                ).fetchall()

                schedule_mix = conn.execute(
                    """
                    SELECT COALESCE(scheduling_type, 'unknown') as schedule_type, COUNT(*) as count
                    FROM processed_tasks
                    GROUP BY COALESCE(scheduling_type, 'unknown')
                    ORDER BY count DESC
                    """
                ).fetchall()

                recent_run = conn.execute(
                    """
                    SELECT schedule_type, total_rows, completed_rows, status, created_at
                    FROM pipeline_runs
                    ORDER BY run_id DESC
                    LIMIT 1
                    """
                ).fetchone()

            return {
                "total_tasks": int(total),
                "avg_execution_time": float(avg_exec),
                "avg_predicted_execution_time": float(avg_pred),
                "avg_priority": float(avg_priority),
                "avg_predicted_server_load": float(avg_load),
                "active_servers": int(active_servers),
                "priority_distribution": [{"band": row[0], "count": row[1]} for row in priority_distribution],
                "server_load_distribution": [{"server": row[0], "count": row[1]} for row in server_load_distribution],
                "schedule_mix": [{"schedule_type": row[0], "count": row[1]} for row in schedule_mix],
                "status": pipeline_status.snapshot(),
                "recent_run": (
                    {
                        "schedule_type": recent_run[0],
                        "total_rows": recent_run[1],
                        "completed_rows": recent_run[2],
                        "status": recent_run[3],
                        "created_at": recent_run[4],
                    }
                    if recent_run
                    else None
                ),
                "degraded": False,
            }
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
            last_exc = exc
            time.sleep(0.35)

    return {
        "total_tasks": int(status.get("rows_processed", 0) or 0),
        "avg_execution_time": 0.0,
        "avg_predicted_execution_time": 0.0,
        "avg_priority": 0.0,
        "avg_predicted_server_load": 0.0,
        "active_servers": 0,
        "priority_distribution": [],
        "server_load_distribution": [],
        "schedule_mix": [],
        "status": status,
        "recent_run": None,
        "degraded": True,
        "degraded_reason": str(last_exc) if last_exc else "temporary_metrics_unavailable",
    }


@router.get("/server-balance")
async def server_balance() -> dict:
    last_exc = None
    for _ in range(2):
        try:
            return get_server_balance()
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
            last_exc = exc
            time.sleep(0.25)

    return {
        "servers": [],
        "remaining_unassigned": 0,
        "server_tree": {"root": "ROOT", "level_order": ["ROOT"], "nodes": []},
        "degraded": True,
        "degraded_reason": str(last_exc) if last_exc else "temporary_server_balance_unavailable",
    }


@router.post("/rebalance-unassigned")
async def rebalance_unassigned(
    auto_scale: bool = True,
    max_rows: int = Query(default=200000, ge=1000, le=2000000),
    batch_size: int = Query(default=25000, ge=1000, le=200000),
) -> dict:
    result = rebalance_unassigned_tasks(
        auto_scale=auto_scale,
        max_rows=max_rows,
        batch_size=batch_size,
    )
    return result
