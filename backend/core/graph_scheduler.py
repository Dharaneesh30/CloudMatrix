from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List


def topological_sort(tasks: List[Dict]) -> List[Dict]:
    """Alias API: dependency-based topological order."""
    return schedule_with_graph(tasks)


def get_execution_order(tasks: List[Dict]) -> List[Dict]:
    """Alias used by demo runner."""
    return schedule_with_graph(tasks)


def schedule_with_graph(tasks: List[Dict]) -> List[Dict]:
    """
    Topological scheduling.
    Supports optional `depends_on` as list[str] in each task.
    """
    if not tasks:
        return []

    task_map = {str(task.get("id")): dict(task) for task in tasks}
    in_degree = defaultdict(int)
    graph = defaultdict(list)

    for task_id in task_map:
        in_degree[task_id] = 0

    for task in tasks:
        curr_id = str(task.get("id"))
        deps = task.get("depends_on", []) or []
        for dep in deps:
            dep_id = str(dep)
            if dep_id in task_map:
                graph[dep_id].append(curr_id)
                in_degree[curr_id] += 1

    q = deque(
        sorted(
            [tid for tid, deg in in_degree.items() if deg == 0],
            key=lambda tid: float(task_map[tid].get("priority_score", task_map[tid].get("priority", 0.0))),
            reverse=True,
        )
    )

    ordered_ids = []
    while q:
        node = q.popleft()
        ordered_ids.append(node)
        for nxt in graph[node]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                q.append(nxt)

    # If cycle exists, append unresolved nodes by priority.
    if len(ordered_ids) < len(task_map):
        unresolved = [tid for tid in task_map if tid not in set(ordered_ids)]
        unresolved.sort(
            key=lambda tid: float(task_map[tid].get("priority_score", task_map[tid].get("priority", 0.0))),
            reverse=True,
        )
        ordered_ids.extend(unresolved)

    result = []
    for rank, tid in enumerate(ordered_ids, start=1):
        row = dict(task_map[tid])
        row["schedule_rank"] = rank
        result.append(row)

    return result
