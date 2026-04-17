from __future__ import annotations

from typing import Dict, List

try:
    from .graph_scheduler import schedule_with_graph
    from .merge_sort import merge_sort_tasks
except ImportError:
    from core.graph_scheduler import schedule_with_graph
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

    # Keep only the latest payload for duplicated ids while preserving order.
    # This is considerably lighter than materializing a custom hash-table object.
    latest_by_id: Dict[str, Dict] = {}
    ordered_ids: List[str] = []
    for idx, task in enumerate(tasks):
        task_id = str(task.get("id") or f"task_{idx}")
        payload = dict(task)
        payload["id"] = task_id
        if task_id not in latest_by_id:
            ordered_ids.append(task_id)
        latest_by_id[task_id] = payload

    return [latest_by_id[task_id] for task_id in ordered_ids]


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

    return merge_sort_tasks(tasks, key="priority_score", reverse=True)
