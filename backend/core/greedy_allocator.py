from __future__ import annotations

from typing import Dict, List, Tuple


def allocate_greedy(tasks: List[Dict], servers: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Best-fit greedy allocation prioritizing least-loaded viable server.
    Returns (allocations, unassigned, updated_servers).
    """
    allocations: List[Dict] = []
    unassigned: List[Dict] = []

    for task in tasks:
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
                score = (cpu_ratio + mem_ratio) / 2
                candidates.append((score, idx))

        if not candidates:
            unassigned.append(
                {
                    "task_id": str(task.get("id")),
                    "reason": "Insufficient server resources",
                }
            )
            continue

        # lower score = less-loaded server, helps balancing
        _, best_idx = min(candidates, key=lambda x: x[0])
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
