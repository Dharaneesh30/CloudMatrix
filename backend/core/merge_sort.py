from __future__ import annotations

from typing import Dict, List


def merge_sort_tasks(tasks: List[Dict], key: str = "priority_score", reverse: bool = True) -> List[Dict]:
    """Stable divide-and-conquer merge sort for task dicts."""
    if len(tasks) <= 1:
        return tasks[:]

    mid = len(tasks) // 2
    left = merge_sort_tasks(tasks[:mid], key=key, reverse=reverse)
    right = merge_sort_tasks(tasks[mid:], key=key, reverse=reverse)
    return _merge(left, right, key=key, reverse=reverse)


def _value(task: Dict, key: str) -> float:
    try:
        return float(task.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _merge(left: List[Dict], right: List[Dict], key: str, reverse: bool) -> List[Dict]:
    merged: List[Dict] = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        left_val = _value(left[i], key)
        right_val = _value(right[j], key)

        if reverse:
            take_left = left_val >= right_val
        else:
            take_left = left_val <= right_val

        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    if i < len(left):
        merged.extend(left[i:])
    if j < len(right):
        merged.extend(right[j:])

    return merged
