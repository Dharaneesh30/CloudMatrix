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
