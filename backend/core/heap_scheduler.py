import heapq
from typing import Dict, List


def schedule_with_heap(tasks: List[Dict]) -> List[Dict]:
    """
    Max-heap scheduler based on priority_score, then priority.
    Returns tasks in execution order with schedule_rank (1..n).
    """

    heap = []
    for task in tasks:
        priority_score = float(task.get("priority_score", 0.0))
        priority = float(task.get("priority", 0.0))
        task_id = str(task.get("id", ""))
        heapq.heappush(heap, (-priority_score, -priority, task_id, task))

    ordered = []
    rank = 1
    while heap:
        _, _, _, task = heapq.heappop(heap)
        scheduled = dict(task)
        scheduled["schedule_rank"] = rank
        ordered.append(scheduled)
        rank += 1

    return ordered
