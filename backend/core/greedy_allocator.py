from __future__ import annotations

import random
from typing import Dict, List, Tuple


def _server_load_ratio(server: Dict) -> float:
    cpu_cap = float(server.get("cpu_capacity", 0.0))
    mem_cap = float(server.get("memory_capacity", 0.0))
    cpu_avail = float(server.get("cpu_available", 0.0))
    mem_avail = float(server.get("memory_available", 0.0))
    cpu_ratio = ((cpu_cap - cpu_avail) / cpu_cap) if cpu_cap else 1.0
    mem_ratio = ((mem_cap - mem_avail) / mem_cap) if mem_cap else 1.0
    return (cpu_ratio + mem_ratio) / 2.0


def _pick_random_balanced_server(candidates: List[Dict], cpu_req: float, mem_req: float) -> Dict:
    # Randomized assignment with load-awareness:
    # keep best-fit quality, randomize only among near-equal top servers.
    scored = []
    for server in candidates:
        cpu_cap = float(server.get("cpu_capacity", 0.0))
        mem_cap = float(server.get("memory_capacity", 0.0))
        cpu_slack = ((float(server.get("cpu_available", 0.0)) - cpu_req) / cpu_cap) if cpu_cap else 0.0
        mem_slack = ((float(server.get("memory_available", 0.0)) - mem_req) / mem_cap) if mem_cap else 0.0
        fit_score = max(0.0, cpu_slack) + max(0.0, mem_slack)
        scored.append((fit_score, _server_load_ratio(server), server))

    scored.sort(key=lambda item: (item[0], item[1]))
    best_fit = scored[0][0]
    window = [item[2] for item in scored if item[0] <= best_fit + 0.05][:4]
    if not window:
        window = [scored[0][2]]

    weights = []
    for server in window:
        cpu_cap = float(server.get("cpu_capacity", 0.0))
        mem_cap = float(server.get("memory_capacity", 0.0))
        cpu_slack = ((float(server.get("cpu_available", 0.0)) - cpu_req) / cpu_cap) if cpu_cap else 0.0
        mem_slack = ((float(server.get("memory_available", 0.0)) - mem_req) / mem_cap) if mem_cap else 0.0
        # more slack + lower load => higher probability
        weight = max(0.05, 1.0 - _server_load_ratio(server) + max(0.0, cpu_slack) + max(0.0, mem_slack))
        weights.append(weight)
    return random.choices(window, weights=weights, k=1)[0]


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
        for server in servers:
            cpu_avail = float(server["cpu_available"])
            mem_avail = float(server["memory_available"])
            if cpu_avail >= cpu_req and mem_avail >= mem_req:
                candidates.append(server)

        if not candidates:
            unassigned.append({"task_id": str(task.get("id"))})
            continue

        best = _pick_random_balanced_server(candidates, cpu_req, mem_req)
        best["cpu_available"] = float(best["cpu_available"]) - cpu_req
        best["memory_available"] = float(best["memory_available"]) - mem_req

        allocations.append(
            {
                "task_id": str(task.get("id")),
                "server_id": str(best["server_id"]),
            }
        )

    return allocations, unassigned, servers
