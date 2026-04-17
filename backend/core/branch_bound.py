from __future__ import annotations

import heapq
from typing import Dict, List, Tuple

def schedule_branch_and_bound(tasks: List[Dict]) -> List[Dict]:
    """
    Branch-and-bound over top-K candidates by priority score.
    Uses lower bound on rank penalty to prune search.
    """
    if not tasks:
        return []

    scored = [
        (float(t.get("priority_score", t.get("priority", 0.0))), dict(t))
        for t in tasks
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Keep search bounded for large datasets.
    search_size = min(len(scored), 40)
    head = scored[:search_size]
    tail = [task for _, task in scored[search_size:]]

    best_order: List[Dict] = [task for _, task in head]
    best_score = _objective(best_order)

    pq: List[Tuple[float, int, List[Dict], List[Dict]]] = []
    # (bound, depth, chosen, remaining)
    heapq.heappush(pq, (0.0, 0, [], [task for _, task in head]))

    expansions = 0
    max_expansions = 2500

    while pq and expansions < max_expansions:
        bound, depth, chosen, remaining = heapq.heappop(pq)
        expansions += 1

        if bound >= best_score:
            continue

        if not remaining:
            score = _objective(chosen)
            if score < best_score:
                best_score = score
                best_order = chosen[:]
            continue

        # Branch on top two high-priority candidates only to keep complexity in check.
        branch_candidates = remaining[:2]
        for candidate in branch_candidates:
            next_chosen = chosen + [candidate]
            next_remaining = [r for r in remaining if r is not candidate]
            next_bound = _lower_bound(next_chosen, next_remaining)
            if next_bound < best_score:
                heapq.heappush(pq, (next_bound, depth + 1, next_chosen, next_remaining))

    ordered = best_order + tail
    result = []
    for rank, task in enumerate(ordered, start=1):
        row = dict(task)
        row["schedule_rank"] = rank
        result.append(row)
    return result

def _objective(order: List[Dict]) -> float:
    # Minimize weighted completion time proxy.
    total = 0.0
    completion = 0.0
    for rank, task in enumerate(order, start=1):
        duration = max(0.1, float(task.get("predicted_execution_time", task.get("execution_time", 1.0))))
        weight = max(0.1, float(task.get("priority_score", task.get("priority", 1.0))))
        completion += duration
        total += completion / weight + (rank * 0.01)
    return total

def _lower_bound(chosen: List[Dict], remaining: List[Dict]) -> float:
    score = _objective(chosen)
    # optimistic continuation: remaining sorted best-first.
    optimistic = sorted(
        remaining,
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )
    return score + (_objective(optimistic) * 0.2)


def optimize_allocation(tasks_subset: List[Dict], servers: List[Dict]) -> Dict[str, str]:
    """
    Branch-and-bound allocation refinement for a small high-priority subset (20-50 tasks).
    Objective: minimize server load imbalance.
    Returns mapping: task_id -> server_id.
    """
    if not tasks_subset or not servers:
        return {}

    bounded_tasks = sorted(
        [dict(t) for t in tasks_subset],
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )[:50]

    base_servers = [
        {
            "server_id": str(s.get("server_id")),
            "cpu_capacity": float(s.get("cpu_capacity", 0.0)),
            "memory_capacity": float(s.get("memory_capacity", 0.0)),
            "cpu_available": float(s.get("cpu_available", 0.0)),
            "memory_available": float(s.get("memory_available", 0.0)),
        }
        for s in servers
    ]

    best_map: Dict[str, str] = {}
    best_score = float("inf")
    expansions = 0
    max_expansions = 1200

    def imbalance_score(state_servers: List[Dict]) -> float:
        ratios = []
        for srv in state_servers:
            cpu_cap = float(srv["cpu_capacity"])
            mem_cap = float(srv["memory_capacity"])
            cpu_used = cpu_cap - float(srv["cpu_available"])
            mem_used = mem_cap - float(srv["memory_available"])
            cpu_ratio = (cpu_used / cpu_cap) if cpu_cap else 1.0
            mem_ratio = (mem_used / mem_cap) if mem_cap else 1.0
            ratios.append((cpu_ratio + mem_ratio) / 2.0)
        if not ratios:
            return 0.0
        mean = sum(ratios) / len(ratios)
        return sum((r - mean) ** 2 for r in ratios) / len(ratios)

    def lower_bound(idx: int, state_servers: List[Dict]) -> float:
        # optimistic bound: current imbalance only
        return imbalance_score(state_servers)

    def recurse(idx: int, state_servers: List[Dict], mapping: Dict[str, str]) -> None:
        nonlocal best_score, best_map, expansions
        if expansions >= max_expansions:
            return
        expansions += 1

        if idx >= len(bounded_tasks):
            score = imbalance_score(state_servers)
            if score < best_score:
                best_score = score
                best_map = dict(mapping)
            return

        if lower_bound(idx, state_servers) >= best_score:
            return

        task = bounded_tasks[idx]
        task_id = str(task.get("id"))
        cpu_req = float(task.get("cpu_request", 0.0))
        mem_req = float(task.get("memory_request", 0.0))

        # least-loaded-first branching
        server_order = sorted(
            range(len(state_servers)),
            key=lambda i: (
                (state_servers[i]["cpu_capacity"] - state_servers[i]["cpu_available"])
                / max(state_servers[i]["cpu_capacity"], 1e-9)
                + (state_servers[i]["memory_capacity"] - state_servers[i]["memory_available"])
                / max(state_servers[i]["memory_capacity"], 1e-9)
            ),
        )

        for idx_srv in server_order[: min(3, len(server_order))]:
            srv = state_servers[idx_srv]
            if srv["cpu_available"] < cpu_req or srv["memory_available"] < mem_req:
                continue

            srv["cpu_available"] -= cpu_req
            srv["memory_available"] -= mem_req
            mapping[task_id] = str(srv["server_id"])

            recurse(idx + 1, state_servers, mapping)

            mapping.pop(task_id, None)
            srv["cpu_available"] += cpu_req
            srv["memory_available"] += mem_req

    recurse(0, base_servers, {})
    return best_map
