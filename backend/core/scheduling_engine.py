from __future__ import annotations

from typing import Dict, List, Tuple

try:
    from .backtracking_allocator import allocate_backtracking
    from .branch_bound import schedule_branch_and_bound
    from .dp_scheduler import schedule_dp
    from .graph_scheduler import schedule_with_graph
    from .greedy_allocator import allocate_greedy
    from .heap_scheduler import schedule_with_heap
    from .merge_sort import merge_sort_tasks
    from .sjf_scheduler import schedule_sjf
except ImportError:
    from backtracking_allocator import allocate_backtracking
    from branch_bound import schedule_branch_and_bound
    from dp_scheduler import schedule_dp
    from graph_scheduler import schedule_with_graph
    from greedy_allocator import allocate_greedy
    from heap_scheduler import schedule_with_heap
    from merge_sort import merge_sort_tasks
    from sjf_scheduler import schedule_sjf


def default_servers(server_count: int = 3) -> List[Dict]:
    count = max(1, int(server_count or 1))
    servers: List[Dict] = []
    for idx in range(1, count + 1):
        servers.append(
            {
                "server_id": f"S{idx}",
                "cpu_capacity": 800.0,
                "memory_capacity": 1600.0,
                "cpu_available": 800.0,
                "memory_available": 1600.0,
            }
        )
    return servers


def resolve_schedule_type(requested_type: str, task_count: int) -> str:
    """
    Performance-aware scheduler resolver.
    Uses faster strategies for large workloads.
    """
    algo = (requested_type or "fast").lower().strip()

    if algo in {"fast", "hybrid"}:
        if task_count <= 22:
            return "backtracking"
        if task_count <= 5000:
            return "branch_bound"
        return "greedy"

    if algo == "backtracking":
        return "backtracking" if task_count <= 22 else "heap"

    if algo in {"branch_bound", "branch-and-bound", "branchbound"}:
        return "branch_bound" if task_count <= 5000 else "heap"

    if algo == "dp":
        return "dp" if task_count <= 20000 else "greedy"

    if algo == "graph":
        return "graph" if task_count <= 50000 else "heap"

    return algo


def schedule_tasks(tasks: List[Dict], schedule_type: str) -> List[Dict]:
    algo = resolve_schedule_type(schedule_type, len(tasks))

    if algo == "heap":
        return schedule_with_heap(tasks)
    if algo == "sjf":
        return schedule_sjf(tasks)
    if algo == "greedy":
        ordered = merge_sort_tasks(tasks, key="priority_score", reverse=True)
        return _with_rank(ordered)
    if algo == "dp":
        return schedule_dp(tasks)
    if algo in {"branch_bound", "branch-and-bound", "branchbound"}:
        return schedule_branch_and_bound(tasks)
    if algo == "backtracking":
        ordered = merge_sort_tasks(tasks, key="priority_score", reverse=True)
        return _with_rank(ordered)
    if algo == "graph":
        return schedule_with_graph(tasks)

    raise ValueError(f"Unsupported schedule type: {schedule_type}")


def allocate_for_schedule(
    scheduled_tasks: List[Dict],
    schedule_type: str,
    servers: List[Dict] | None = None,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    if servers is None:
        servers = default_servers()

    algo = resolve_schedule_type(schedule_type, len(scheduled_tasks))

    if algo == "backtracking" and len(scheduled_tasks) <= 22:
        allocations, unassigned, updated_servers = allocate_backtracking(scheduled_tasks, servers)
        if not unassigned:
            return allocations, unassigned, updated_servers

        # Ensure all tasks are allocated by falling back to greedy autoscale for unresolved tasks.
        unassigned_ids = {str(item.get("task_id")) for item in unassigned}
        fallback_tasks = [task for task in scheduled_tasks if str(task.get("id")) in unassigned_ids]
        extra_allocations, extra_unassigned, final_servers = allocate_greedy(fallback_tasks, updated_servers)
        return allocations + extra_allocations, extra_unassigned, final_servers

    return allocate_greedy(scheduled_tasks, servers)


def _with_rank(tasks: List[Dict]) -> List[Dict]:
    out = []
    for rank, task in enumerate(tasks, start=1):
        row = dict(task)
        row["schedule_rank"] = rank
        out.append(row)
    return out
