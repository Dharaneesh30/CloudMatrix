from __future__ import annotations

from typing import Dict, List, Tuple


MAX_BACKTRACK_TASKS = 22


def allocate_backtracking(tasks: List[Dict], servers: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Exact-search allocator for small batches."""
    if len(tasks) > MAX_BACKTRACK_TASKS:
        # keep runtime bounded; caller can fallback
        return [], [{"task_id": str(t.get("id")), "reason": "batch_too_large"} for t in tasks], servers

    ordered_tasks = sorted(
        tasks,
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )

    best_assignment: List[Tuple[str, str]] = []

    def recurse(idx: int, current: List[Tuple[str, str]]) -> None:
        nonlocal best_assignment

        if idx == len(ordered_tasks):
            if len(current) > len(best_assignment):
                best_assignment = current[:]
            return

        if len(current) + (len(ordered_tasks) - idx) <= len(best_assignment):
            return

        task = ordered_tasks[idx]
        cpu_req = float(task.get("cpu_request", 0.0))
        mem_req = float(task.get("memory_request", 0.0))

        assigned = False
        for server in servers:
            if server["cpu_available"] >= cpu_req and server["memory_available"] >= mem_req:
                assigned = True
                server["cpu_available"] -= cpu_req
                server["memory_available"] -= mem_req
                current.append((str(task.get("id")), str(server["server_id"])))

                recurse(idx + 1, current)

                current.pop()
                server["cpu_available"] += cpu_req
                server["memory_available"] += mem_req

        if not assigned:
            recurse(idx + 1, current)

    recurse(0, [])

    assignment_map = {task_id: server_id for task_id, server_id in best_assignment}
    allocations = []
    unassigned = []

    for task in ordered_tasks:
        task_id = str(task.get("id"))
        if task_id in assignment_map:
            server_id = assignment_map[task_id]
            allocations.append({"task_id": task_id, "server_id": server_id})
            for server in servers:
                if str(server["server_id"]) == server_id:
                    server["cpu_available"] -= float(task.get("cpu_request", 0.0))
                    server["memory_available"] -= float(task.get("memory_request", 0.0))
                    break
        else:
            unassigned.append({"task_id": task_id, "reason": "No feasible assignment"})

    return allocations, unassigned, servers
