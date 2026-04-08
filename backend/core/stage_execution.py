from __future__ import annotations

from typing import Dict, List, Tuple

try:
    from .dp_scheduler import schedule_dp
    from .heap_scheduler import schedule_with_heap
except ImportError:
    from core.dp_scheduler import schedule_dp
    from core.heap_scheduler import schedule_with_heap


def execute_stage_4_to_6(
    tasks: List[Dict],
    servers: List[Dict],
) -> Tuple[List[Dict], List[Dict], int]:
    """
    Stage 4: Heap-based scheduling queue.
    Stage 5: Greedy server allocation.
    Stage 6: DP-based load optimization over ordered tasks.
    """
    heap_scheduled = _stage_4_schedule_with_heap(tasks)
    allocated_tasks, updated_servers, unassigned_count = _stage_5_allocate_greedy(heap_scheduled, servers)
    optimized_tasks = _stage_6_optimize_with_dp(allocated_tasks)
    return optimized_tasks, updated_servers, unassigned_count


def _stage_4_schedule_with_heap(tasks: List[Dict]) -> List[Dict]:
    if not tasks:
        return []
    return schedule_with_heap(tasks)


def _stage_5_allocate_greedy(
    tasks: List[Dict],
    servers: List[Dict],
) -> Tuple[List[Dict], List[Dict], int]:
    allocations, unassigned, updated_servers = _allocate_greedy_with_autoscale(tasks, servers)
    alloc_map = {str(item["task_id"]): str(item["server_id"]) for item in allocations}
    unassigned_ids = {str(item["task_id"]) for item in unassigned}

    allocated_rows: List[Dict] = []
    for task in tasks:
        row = dict(task)
        task_id = str(row.get("id"))
        row["allocated_server"] = alloc_map.get(task_id)
        row["allocation_success"] = 0 if task_id in unassigned_ids else 1
        allocated_rows.append(row)

    return allocated_rows, updated_servers, len(unassigned)


def _stage_6_optimize_with_dp(tasks: List[Dict]) -> List[Dict]:
    if not tasks:
        return []

    optimized = schedule_dp(tasks)
    for row in optimized:
        row["optimization_stage"] = "dp"
    return optimized


def _server_load_ratio(server: Dict) -> float:
    cpu_cap = float(server.get("cpu_capacity", 0.0))
    mem_cap = float(server.get("memory_capacity", 0.0))
    cpu_avail = float(server.get("cpu_available", 0.0))
    mem_avail = float(server.get("memory_available", 0.0))
    cpu_ratio = ((cpu_cap - cpu_avail) / cpu_cap) if cpu_cap else 1.0
    mem_ratio = ((mem_cap - mem_avail) / mem_cap) if mem_cap else 1.0
    return (cpu_ratio + mem_ratio) / 2


def _new_auto_server_id(servers: List[Dict]) -> str:
    existing = {
        str(server.get("server_id", ""))
        for server in servers
        if str(server.get("server_id", "")).startswith("AUTO_")
    }
    idx = 1
    while f"AUTO_{idx}" in existing:
        idx += 1
    return f"AUTO_{idx}"


def _allocate_greedy_with_autoscale(
    tasks: List[Dict],
    servers: List[Dict],
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Greedy list scheduling with autoscaling:
    if all servers are overloaded for a task, create an AUTO_* server and place it there.
    """
    allocations: List[Dict] = []
    unassigned: List[Dict] = []

    for task in tasks:
        cpu_req = float(task.get("cpu_request", 0.0))
        mem_req = float(task.get("memory_request", 0.0))

        candidates = [
            server
            for server in servers
            if float(server.get("cpu_available", 0.0)) >= cpu_req
            and float(server.get("memory_available", 0.0)) >= mem_req
        ]

        if not candidates:
            auto_cpu = max(2000.0, cpu_req * 50.0)
            auto_mem = max(4000.0, mem_req * 50.0)
            auto_server = {
                "server_id": _new_auto_server_id(servers),
                "cpu_capacity": auto_cpu,
                "memory_capacity": auto_mem,
                "cpu_available": auto_cpu,
                "memory_available": auto_mem,
            }
            servers.append(auto_server)
            candidates = [auto_server]

        best = min(candidates, key=_server_load_ratio)
        best["cpu_available"] = float(best.get("cpu_available", 0.0)) - cpu_req
        best["memory_available"] = float(best.get("memory_available", 0.0)) - mem_req
        allocations.append({"task_id": str(task.get("id")), "server_id": str(best.get("server_id"))})

    return allocations, unassigned, servers
