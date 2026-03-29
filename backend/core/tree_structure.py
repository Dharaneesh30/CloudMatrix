from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ServerNode:
    server_id: str
    cpu_capacity: float
    memory_capacity: float
    cpu_available: float
    memory_available: float
    children: List["ServerNode"] = field(default_factory=list)

    @property
    def load_ratio(self) -> float:
        cpu_used = self.cpu_capacity - self.cpu_available
        mem_used = self.memory_capacity - self.memory_available
        cpu_ratio = (cpu_used / self.cpu_capacity) if self.cpu_capacity else 1.0
        mem_ratio = (mem_used / self.memory_capacity) if self.memory_capacity else 1.0
        return (cpu_ratio + mem_ratio) / 2


def build_server_hierarchy(servers: List[Dict]) -> ServerNode:
    """
    Builds a minimal two-level tree.
    root
      -> server nodes
    """
    root = ServerNode(
        server_id="ROOT",
        cpu_capacity=0,
        memory_capacity=0,
        cpu_available=0,
        memory_available=0,
    )

    for server in servers:
        root.children.append(
            ServerNode(
                server_id=str(server["server_id"]),
                cpu_capacity=float(server["cpu_capacity"]),
                memory_capacity=float(server["memory_capacity"]),
                cpu_available=float(server.get("cpu_available", server["cpu_capacity"])),
                memory_available=float(server.get("memory_available", server["memory_capacity"])),
            )
        )

    return root


def flatten_servers(root: ServerNode) -> List[Dict]:
    return [
        {
            "server_id": node.server_id,
            "cpu_capacity": node.cpu_capacity,
            "memory_capacity": node.memory_capacity,
            "cpu_available": node.cpu_available,
            "memory_available": node.memory_available,
            "load_ratio": node.load_ratio,
        }
        for node in root.children
    ]
