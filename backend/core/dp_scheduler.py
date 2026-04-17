from __future__ import annotations

from typing import Dict, List


def optimize_tasks(tasks_subset: List[Dict]) -> List[Dict]:
    """
    Knapsack-style optimization on a bounded subset only (top 500-1000 tasks).
    Returns optimized execution order for the subset.
    """
    if not tasks_subset:
        return []

    scored = sorted(
        [dict(task) for task in tasks_subset],
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )

    # Explicit subset safety gate for scalability.
    dp_candidates = scored[:1000]
    tail = scored[1000:]

    max_cpu = max(1.0, max(float(t.get("cpu_request", 1.0) or 1.0) for t in dp_candidates))
    scale = max(1.0, max_cpu / 20.0)
    weights = [max(1, int(round(float(t.get("cpu_request", 1.0) or 1.0) / scale))) for t in dp_candidates]
    values = [max(0.0, float(t.get("priority_score", t.get("priority", 0.0) or 0.0))) for t in dp_candidates]

    total_weight = sum(weights)
    capacity = max(1, int(total_weight * 0.35))

    n = len(dp_candidates)
    table = [[0.0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        prev = table[i - 1]
        curr = table[i]
        for cap in range(capacity + 1):
            best = prev[cap]
            if w <= cap:
                pick = prev[cap - w] + v
                if pick > best:
                    best = pick
            curr[cap] = best

    selected_ids = set()
    cap = capacity
    for i in range(n, 0, -1):
        if table[i][cap] != table[i - 1][cap]:
            task = dp_candidates[i - 1]
            selected_ids.add(str(task.get("id")))
            cap -= weights[i - 1]
            if cap <= 0:
                break

    selected = []
    deferred = []
    for task in dp_candidates:
        if str(task.get("id")) in selected_ids:
            selected.append(task)
        else:
            deferred.append(task)

    ordered = selected + sorted(
        deferred + tail,
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )

    out = []
    for rank, task in enumerate(ordered, start=1):
        row = dict(task)
        row["schedule_rank"] = rank
        out.append(row)
    return out


def optimize_schedule(tasks: List[Dict]) -> Dict:
    """
    Demo-friendly DP summary API.
    """
    ordered = optimize_tasks(tasks[:1000])
    selected = ordered[: max(1, int(len(ordered) * 0.35))]
    deferred = ordered[len(selected) :]
    return {
        "time_budget": len(selected),
        "selected_tasks": selected,
        "deferred_tasks": deferred,
    }


def schedule_dp(tasks: List[Dict]) -> List[Dict]:
    """
    Knapsack-style dynamic programming scheduler.
    Selects a high-value subset first under a computed CPU budget, then appends the rest.
    """
    if not tasks:
        return []

    return optimize_tasks(tasks[:500])
