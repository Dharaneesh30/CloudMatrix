from __future__ import annotations

from typing import Dict, List

import pandas as pd

try:
    from .graph_scheduler import schedule_with_graph
    from .hash_table import HashTable
    from .merge_sort import merge_sort_tasks
except ImportError:
    from core.graph_scheduler import schedule_with_graph
    from core.hash_table import HashTable
    from core.merge_sort import merge_sort_tasks


def preprocess_tasks_stage_1_to_3(tasks: List[Dict]) -> List[Dict]:
    """
    Stage 1: Hash table storage for O(1) task-id lookup.
    Stage 2: Graph-based dependency resolution (topological ordering when dependencies exist).
    Stage 3: Divide-and-conquer merge sort plus pandas stable sort optimization.
    """
    stored_tasks = _stage_1_store_in_hash_table(tasks)
    dependency_ordered = _stage_2_apply_topological_order(stored_tasks)
    return _stage_3_prioritize_tasks(dependency_ordered)


def _stage_1_store_in_hash_table(tasks: List[Dict]) -> List[Dict]:
    if not tasks:
        return []

    table = HashTable(capacity=max(2048, len(tasks) * 2))
    for idx, task in enumerate(tasks):
        task_id = str(task.get("id") or f"task_{idx}")
        table.put(task_id, dict(task))

    # Materialize back to list after O(1)-friendly keyed storage.
    return [value for _, value in table.items()]


def _stage_2_apply_topological_order(tasks: List[Dict]) -> List[Dict]:
    if not tasks:
        return []

    has_dependencies = any(bool(task.get("depends_on")) for task in tasks)
    if not has_dependencies:
        return tasks

    ordered = schedule_with_graph(tasks)
    for task in ordered:
        task.pop("schedule_rank", None)
    return ordered


def _stage_3_prioritize_tasks(tasks: List[Dict]) -> List[Dict]:
    if not tasks:
        return []

    merge_sorted = merge_sort_tasks(tasks, key="priority_score", reverse=True)
    df = pd.DataFrame(merge_sorted)
    if df.empty:
        return merge_sorted

    if "priority_score" not in df.columns:
        df["priority_score"] = 0.0
    if "priority" not in df.columns:
        df["priority"] = 0.0

    # Keep merge-sort order as a deterministic tiebreaker.
    df["_merge_pos"] = range(len(df))
    df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0.0)
    df["priority"] = pd.to_numeric(df["priority"], errors="coerce").fillna(0.0)

    df = df.sort_values(
        by=["priority_score", "priority", "_merge_pos"],
        ascending=[False, False, True],
        kind="mergesort",
    )

    return df.drop(columns=["_merge_pos"], errors="ignore").to_dict(orient="records")
