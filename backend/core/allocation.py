from __future__ import annotations

from typing import Dict, List

try:
    from .greedy_allocator import allocate_greedy
except ImportError:
    from greedy_allocator import allocate_greedy


def greedy_allocate(tasks: List[Dict], servers=None):
    if servers is None:
        servers = [
            {"server_id": "S1", "cpu_capacity": 1.0, "memory_capacity": 1.0, "cpu_available": 1.0, "memory_available": 1.0},
            {"server_id": "S2", "cpu_capacity": 1.0, "memory_capacity": 1.0, "cpu_available": 1.0, "memory_available": 1.0},
            {"server_id": "S3", "cpu_capacity": 1.0, "memory_capacity": 1.0, "cpu_available": 1.0, "memory_available": 1.0},
        ]
    allocations, unassigned, updated_servers = allocate_greedy(tasks, servers)
    return {
        "allocations": allocations,
        "unassigned": unassigned,
        "servers": updated_servers,
    }
