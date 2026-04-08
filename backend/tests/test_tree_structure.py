import unittest

from backend.core.tree_structure import (
    TaskPriorityBST,
    build_server_hierarchy,
    flatten_servers,
    level_order_server_ids,
)


class TreeStructureTests(unittest.TestCase):
    def test_server_hierarchy_level_order_and_flatten(self):
        servers = [
            {"server_id": "S1", "cpu_capacity": 100, "memory_capacity": 200, "cpu_available": 80, "memory_available": 150},
            {"server_id": "S2", "cpu_capacity": 100, "memory_capacity": 200, "cpu_available": 70, "memory_available": 140},
        ]
        root = build_server_hierarchy(servers)
        level = level_order_server_ids(root)
        flat = flatten_servers(root)

        self.assertEqual(level[0], "ROOT")
        self.assertEqual(len(flat), 2)
        self.assertEqual(flat[0]["server_id"], "S1")

    def test_task_priority_bst_insert_search_and_inorder(self):
        bst = TaskPriorityBST()
        bst.insert({"id": "t1", "priority_score": 5})
        bst.insert({"id": "t2", "priority_score": 9})
        bst.insert({"id": "t3", "priority_score": 3})

        self.assertIsNotNone(bst.search("t2"))
        self.assertIsNone(bst.search("missing"))

        asc = bst.inorder(descending=False)
        desc = bst.inorder(descending=True)
        self.assertEqual([x["id"] for x in asc], ["t3", "t1", "t2"])
        self.assertEqual([x["id"] for x in desc], ["t2", "t1", "t3"])


if __name__ == "__main__":
    unittest.main()
