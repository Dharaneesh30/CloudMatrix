from __future__ import annotations

from typing import Dict, List

try:
    from .merge_sort import merge_sort_tasks
except ImportError:
    from merge_sort import merge_sort_tasks


def merge_sort(tasks: List[Dict]) -> List[Dict]:
    return merge_sort_tasks(tasks, key="priority", reverse=False)
