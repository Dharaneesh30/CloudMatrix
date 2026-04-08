from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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

    def add_child(self, child: "ServerNode") -> None:
        self.children.append(child)


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
        root.add_child(
            ServerNode(
                server_id=str(server.get("server_id", "unknown")),
                cpu_capacity=float(server.get("cpu_capacity", 0.0)),
                memory_capacity=float(server.get("memory_capacity", 0.0)),
                cpu_available=float(server.get("cpu_available", server.get("cpu_capacity", 0.0))),
                memory_available=float(server.get("memory_available", server.get("memory_capacity", 0.0))),
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


def level_order_server_ids(root: ServerNode) -> List[str]:
    """Breadth-first traversal over server hierarchy."""
    order: List[str] = []
    queue: List[ServerNode] = [root]
    while queue:
        node = queue.pop(0)
        order.append(node.server_id)
        queue.extend(node.children)
    return order


@dataclass
class TaskTreeNode:
    task_id: str
    priority_score: float
    payload: Dict
    left: Optional["TaskTreeNode"] = None
    right: Optional["TaskTreeNode"] = None


class TaskPriorityBST:
    """
    Basic Binary Search Tree for task priorities.
    Smaller priority_score goes left, larger goes right.
    """

    def __init__(self) -> None:
        self.root: Optional[TaskTreeNode] = None

    def insert(self, task: Dict) -> None:
        task_id = str(task.get("id", "unknown"))
        score = float(task.get("priority_score", task.get("priority", 0.0)) or 0.0)
        node = TaskTreeNode(task_id=task_id, priority_score=score, payload=dict(task))
        if self.root is None:
            self.root = node
            return

        current = self.root
        while True:
            if (score, task_id) < (current.priority_score, current.task_id):
                if current.left is None:
                    current.left = node
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = node
                    return
                current = current.right

    def search(self, task_id: str) -> Optional[Dict]:
        # DFS stack search by id (BST is keyed by score, so id lookup is not ordered).
        if self.root is None:
            return None
        stack: List[TaskTreeNode] = [self.root]
        while stack:
            node = stack.pop()
            if node.task_id == task_id:
                return dict(node.payload)
            if node.right is not None:
                stack.append(node.right)
            if node.left is not None:
                stack.append(node.left)
        return None

    def inorder(self, descending: bool = False) -> List[Dict]:
        out: List[Dict] = []

        def walk(node: Optional[TaskTreeNode]) -> None:
            if node is None:
                return
            first, second = (node.right, node.left) if descending else (node.left, node.right)
            walk(first)
            out.append(dict(node.payload))
            walk(second)

        walk(self.root)
        return out
