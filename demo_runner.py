from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.core.branch_bound import optimize_allocation, schedule_branch_and_bound
from backend.core.dp_scheduler import optimize_tasks
from backend.core.graph_scheduler import topological_sort
from backend.core.greedy_allocator import allocate_tasks
from backend.core.hash_table import HashTable
from backend.core.heap_scheduler import get_next_task, schedule_with_heap
from backend.core.merge_sort import merge_sort_tasks
from backend.core.scheduling_engine import default_servers
from backend.core.tree_structure import assign_to_tree


def sample_tasks() -> list[dict]:
    return [
        {"id": "T1", "priority": 9, "cpu_request": 20, "memory_request": 40, "execution_time": 5, "priority_score": 82},
        {"id": "T2", "priority": 6, "cpu_request": 30, "memory_request": 50, "execution_time": 7, "priority_score": 65, "depends_on": ["T1"]},
        {"id": "T3", "priority": 8, "cpu_request": 15, "memory_request": 30, "execution_time": 4, "priority_score": 78},
        {"id": "T4", "priority": 4, "cpu_request": 35, "memory_request": 70, "execution_time": 9, "priority_score": 49, "depends_on": ["T2"]},
        {"id": "T5", "priority": 7, "cpu_request": 25, "memory_request": 45, "execution_time": 6, "priority_score": 71},
        {"id": "T6", "priority": 5, "cpu_request": 40, "memory_request": 80, "execution_time": 10, "priority_score": 53},
        {"id": "T7", "priority": 10, "cpu_request": 20, "memory_request": 35, "execution_time": 3, "priority_score": 90},
        {"id": "T8", "priority": 3, "cpu_request": 18, "memory_request": 28, "execution_time": 4, "priority_score": 40},
        {"id": "T9", "priority": 8, "cpu_request": 22, "memory_request": 36, "execution_time": 5, "priority_score": 76, "depends_on": ["T3"]},
        {"id": "T10", "priority": 6, "cpu_request": 28, "memory_request": 48, "execution_time": 7, "priority_score": 62},
        {"id": "T11", "priority": 7, "cpu_request": 24, "memory_request": 42, "execution_time": 6, "priority_score": 69},
        {"id": "T12", "priority": 2, "cpu_request": 10, "memory_request": 20, "execution_time": 2, "priority_score": 30},
    ]


def _ids(rows: list[dict], key: str = "id") -> list[str]:
    return [str(r.get(key, "?")) for r in rows]


def main() -> None:
    tasks = sample_tasks()
    servers = default_servers(3)

    print("=== MERGE SORT ===")
    sorted_tasks = merge_sort_tasks(tasks, key="priority_score", reverse=True)
    print(_ids(sorted_tasks))
    print()

    print("=== HEAP SCHEDULING ===")
    heap_order = schedule_with_heap(sorted_tasks)
    print("Next task:", (get_next_task(heap_order) or {}).get("id"))
    print("Order:", _ids(heap_order))
    print()

    print("=== GREEDY ALLOCATION ===")
    allocations, unassigned, updated_servers = allocate_tasks(heap_order, servers)
    print("Allocations:", allocations[:8], "...")
    print("Unassigned:", unassigned)
    print()

    print("=== HASH SEARCH ===")
    table = HashTable(capacity=64)
    for task in tasks:
        table.insert(task)
    target = "T7"
    found = table.search(target)
    print(f"search({target}) ->", "FOUND" if found else "NOT FOUND")
    print()

    print("=== GRAPH ORDER ===")
    graph_order = topological_sort(tasks)
    print(_ids(graph_order))
    print()

    print("=== DP OPTIMIZATION ===")
    dp_order = optimize_tasks(heap_order[:1000])
    print("Top optimized IDs:", _ids(dp_order[:8]))
    print()

    print("=== BRANCH & BOUND ===")
    ranked_subset = schedule_branch_and_bound(heap_order[:40])
    refined_alloc = optimize_allocation(ranked_subset[:50], updated_servers)
    print("Ranked IDs:", _ids(ranked_subset[:8]))
    print("Refined allocations:", list(refined_alloc.items())[:8])
    print()

    print("=== TREE ASSIGNMENT ===")
    alloc_map = {str(a["task_id"]): str(a["server_id"]) for a in allocations}
    enriched = []
    for task in heap_order:
        row = dict(task)
        row["allocated_server"] = alloc_map.get(str(row.get("id")))
        enriched.append(row)
    tree = assign_to_tree(enriched, updated_servers)
    print("Datacenter:", tree.get("datacenter"))
    print("Servers in tree:", [s.get("server_id") for s in tree.get("servers", [])])


if __name__ == "__main__":
    main()

