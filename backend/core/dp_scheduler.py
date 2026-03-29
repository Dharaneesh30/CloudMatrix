from __future__ import annotations

from typing import Dict, List


def schedule_dp(tasks: List[Dict]) -> List[Dict]:
    """
    Weighted interval scheduling on predicted execution windows.
    Falls back gracefully when timing windows overlap heavily.
    """
    if not tasks:
        return []

    jobs = []
    cumulative_time = 0.0
    for task in tasks:
        duration = max(0.1, float(task.get("predicted_execution_time", task.get("execution_time", 1.0))))
        start = cumulative_time
        finish = cumulative_time + duration
        weight = float(task.get("priority_score", task.get("priority", 0.0)))
        jobs.append((start, finish, weight, task))
        cumulative_time += duration

    jobs.sort(key=lambda x: x[1])
    n = len(jobs)

    p = [0] * n
    for i in range(n):
        p[i] = -1
        for j in range(i - 1, -1, -1):
            if jobs[j][1] <= jobs[i][0]:
                p[i] = j
                break

    dp = [0.0] * n
    choose = [False] * n

    for i in range(n):
        include_val = jobs[i][2] + (dp[p[i]] if p[i] >= 0 else 0.0)
        exclude_val = dp[i - 1] if i > 0 else 0.0
        if include_val >= exclude_val:
            dp[i] = include_val
            choose[i] = True
        else:
            dp[i] = exclude_val

    chosen = []
    i = n - 1
    while i >= 0:
        if choose[i]:
            chosen.append(jobs[i][3])
            i = p[i]
        else:
            i -= 1

    chosen_ids = {str(t.get("id")) for t in chosen}
    selected = [t for t in tasks if str(t.get("id")) in chosen_ids]
    remaining = [t for t in tasks if str(t.get("id")) not in chosen_ids]

    ordered = selected + sorted(
        remaining,
        key=lambda t: float(t.get("priority_score", t.get("priority", 0.0))),
        reverse=True,
    )

    result = []
    for rank, task in enumerate(ordered, start=1):
        row = dict(task)
        row["schedule_rank"] = rank
        result.append(row)
    return result
