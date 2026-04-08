from __future__ import annotations

from typing import Dict, List


def schedule_sjf(tasks: List[Dict]) -> List[Dict]:
    """
    Shortest Job First (SJF) scheduling.
    Orders tasks by predicted execution time (or execution_time fallback), shortest first.
    """
    if not tasks:
        return []

    def duration(task: Dict) -> float:
        try:
            return max(
                0.0,
                float(task.get("predicted_execution_time", task.get("execution_time", 0.0))),
            )
        except (TypeError, ValueError):
            return 0.0

    ordered = sorted(
        tasks,
        key=lambda task: (
            duration(task),
            -float(task.get("priority", 0.0) or 0.0),
            str(task.get("id", "")),
        ),
    )

    result = []
    for rank, task in enumerate(ordered, start=1):
        row = dict(task)
        row["schedule_rank"] = rank
        result.append(row)
    return result
