from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent
CORE_DIR = ROOT_DIR / "backend" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from dp_scheduler import optimize_schedule  # noqa: E402
from graph_scheduler import get_execution_order  # noqa: E402
from greedy_allocator import allocate_tasks  # noqa: E402
from hash_table import HashTable  # noqa: E402
from heap_scheduler import schedule_tasks  # noqa: E402
from merge_sort import merge_sort_tasks  # noqa: E402


def sample_tasks() -> list[dict]:
    return [
        {"id": "T1", "priority": 9, "cpu_request": 20, "memory_request": 40, "execution_time": 5, "priority_score": 82},
        {"id": "T2", "priority": 6, "cpu_request": 30, "memory_request": 50, "execution_time": 7, "priority_score": 65},
        {"id": "T3", "priority": 8, "cpu_request": 15, "memory_request": 30, "execution_time": 4, "priority_score": 78},
        {"id": "T4", "priority": 4, "cpu_request": 35, "memory_request": 70, "execution_time": 9, "priority_score": 49},
        {"id": "T5", "priority": 7, "cpu_request": 25, "memory_request": 45, "execution_time": 6, "priority_score": 71},
        {"id": "T6", "priority": 5, "cpu_request": 40, "memory_request": 80, "execution_time": 10, "priority_score": 53},
        {"id": "T7", "priority": 10, "cpu_request": 20, "memory_request": 35, "execution_time": 3, "priority_score": 90},
        {"id": "T8", "priority": 3, "cpu_request": 18, "memory_request": 28, "execution_time": 4, "priority_score": 40},
        {"id": "T9", "priority": 8, "cpu_request": 22, "memory_request": 36, "execution_time": 5, "priority_score": 76},
        {"id": "T10", "priority": 6, "cpu_request": 28, "memory_request": 48, "execution_time": 7, "priority_score": 62},
        {"id": "T11", "priority": 7, "cpu_request": 24, "memory_request": 42, "execution_time": 6, "priority_score": 69},
        {"id": "T12", "priority": 2, "cpu_request": 10, "memory_request": 20, "execution_time": 2, "priority_score": 30},
    ]


def ids(rows: list[dict]) -> list[str]:
    return [str(r.get("id", r.get("task_id", "?"))) for r in rows]


def main() -> None:
    tasks = sample_tasks()

    print("=== MERGE SORT (ALREADY DONE) ===")
    merge_sorted = merge_sort_tasks(tasks, key="priority_score", reverse=True)
    print(ids(merge_sorted))
    print()

    print("=== HEAP SCHEDULING ===")
    heap_order = schedule_tasks(tasks)
    print(ids(heap_order))
    print()

    print("=== GREEDY ALLOCATION ===")
    allocation = allocate_tasks(heap_order)
    print("Allocations:", allocation["allocations"][:8], "...")
    print("Unassigned:", allocation["unassigned"])
    print()

    print("=== HASH TABLE SEARCH ===")
    table = HashTable(capacity=32)
    for task in tasks:
        table.insert(task)
    search_id = "T7"
    found = table.search(search_id)
    print(f"Search Task ID: {search_id} -> {'Found' if found else 'Not Found'}")
    print()

    print("=== GRAPH TOPOLOGICAL ORDER ===")
    graph_order = get_execution_order(tasks)
    print(ids(graph_order))
    print()

    print("=== DP OPTIMIZATION ===")
    optimized = optimize_schedule(tasks)
    print("Time Budget:", optimized["time_budget"])
    print("Selected:", ids(optimized["selected_tasks"]))
    print("Deferred:", ids(optimized["deferred_tasks"]))


if __name__ == "__main__":
    main()
