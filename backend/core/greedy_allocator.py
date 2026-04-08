from __future__ import annotations

from typing import Dict, List, Tuple


def allocate_greedy(tasks: List[Dict], servers: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Best-Fit Decreasing allocation (2D CPU+Memory).
    1) Sort tasks by resource demand (decreasing)
    2) Place each task into feasible server with minimum post-placement slack
    Returns (allocations, unassigned, updated_servers).
    """
    allocations: List[Dict] = []
    unassigned: List[Dict] = []

    ordered_tasks = sorted(
        tasks,
        key=lambda t: (
            float(t.get("cpu_request", 0.0)) + float(t.get("memory_request", 0.0)),
            float(t.get("priority_score", t.get("priority", 0.0))),
        ),
        reverse=True,
    )

    for task in ordered_tasks:
        cpu_req = float(task.get("cpu_request", 0.0))
        mem_req = float(task.get("memory_request", 0.0))

        candidates = []
        for idx, server in enumerate(servers):
            cpu_avail = float(server["cpu_available"])
            mem_avail = float(server["memory_available"])
            if cpu_avail >= cpu_req and mem_avail >= mem_req:
                cpu_cap = float(server["cpu_capacity"])
                mem_cap = float(server["memory_capacity"])
                cpu_ratio = ((cpu_cap - cpu_avail) / cpu_cap) if cpu_cap else 1.0
                mem_ratio = ((mem_cap - mem_avail) / mem_cap) if mem_cap else 1.0
                load_score = (cpu_ratio + mem_ratio) / 2

                # Best-fit objective: minimize leftover normalized capacity after assignment.
                cpu_slack = ((cpu_avail - cpu_req) / cpu_cap) if cpu_cap else 1.0
                mem_slack = ((mem_avail - mem_req) / mem_cap) if mem_cap else 1.0
                fit_score = max(0.0, cpu_slack) + max(0.0, mem_slack)
                candidates.append((fit_score, load_score, idx))

        if not candidates:
            unassigned.append(
                {
                    "task_id": str(task.get("id")),
                    "reason": "Insufficient server resources",
                }
            )
            continue

        # lower fit_score = tighter fit, tie-break by lower current load
        _, _, best_idx = min(candidates, key=lambda x: (x[0], x[1]))
        server = servers[best_idx]
        server["cpu_available"] = float(server["cpu_available"]) - cpu_req
        server["memory_available"] = float(server["memory_available"]) - mem_req

        allocations.append(
            {
                "task_id": str(task.get("id")),
                "server_id": str(server["server_id"]),
            }
        )

    return allocations, unassigned, servers
