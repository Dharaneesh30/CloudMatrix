from __future__ import annotations

from typing import Dict, List

def schedule_dp(tasks: List[Dict]) -> List[Dict]:
    """
    Knapsack-style dynamic programming scheduler.
    Selects a high-value subset first under a computed CPU budget, then appends the rest.
    """
    if not tasks:
        return []

    scored = sorted(
        [dict(task) for task in tasks],
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )

    # Keep DP bounded for responsiveness on very large inputs.
    # Remaining tasks are appended with greedy ordering.
    dp_candidates = scored[:350]
    tail = scored[350:]

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
        for cap in range(capacity + 1):
            best = table[i - 1][cap]
            if w <= cap:
                pick = table[i - 1][cap - w] + v
                if pick > best:
                    best = pick
            table[i][cap] = best

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
    remaining = []
    for task in dp_candidates:
        if str(task.get("id")) in selected_ids:
            selected.append(task)
        else:
            remaining.append(task)

    ordered = selected + sorted(
        remaining + tail,
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )

    result = []
    for rank, task in enumerate(ordered, start=1):
        row = dict(task)
        row["schedule_rank"] = rank
        result.append(row)
    return result
