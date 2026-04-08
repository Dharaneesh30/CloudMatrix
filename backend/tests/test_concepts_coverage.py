import unittest

from backend.core.backtracking_allocator import allocate_backtracking
from backend.core.branch_bound import schedule_branch_and_bound
from backend.core.dp_scheduler import schedule_dp
from backend.core.greedy_allocator import allocate_greedy
from backend.core.hash_table import HashTable
from backend.core.merge_sort import merge_sort_tasks


class ConceptCoverageTests(unittest.TestCase):
    def test_divide_and_conquer_merge_sort(self):
        tasks = [
            {"id": "t1", "priority_score": 2},
            {"id": "t2", "priority_score": 9},
            {"id": "t3", "priority_score": 5},
        ]
        ordered = merge_sort_tasks(tasks, key="priority_score", reverse=True)
        self.assertEqual([t["id"] for t in ordered], ["t2", "t3", "t1"])

    def test_hashing_table_put_get_delete_resize(self):
        table = HashTable(capacity=16)
        for i in range(80):
            table.put(f"k{i}", i)
        self.assertGreaterEqual(table.capacity, 32)
        self.assertEqual(table.get("k10"), 10)
        self.assertTrue(table.delete("k10"))
        self.assertIsNone(table.get("k10"))

    def test_greedy_best_fit_picks_tighter_server_fit(self):
        servers = [
            {
                "server_id": "S1",
                "cpu_capacity": 100.0,
                "memory_capacity": 100.0,
                "cpu_available": 30.0,
                "memory_available": 30.0,
            },
            {
                "server_id": "S2",
                "cpu_capacity": 100.0,
                "memory_capacity": 100.0,
                "cpu_available": 90.0,
                "memory_available": 90.0,
            },
        ]
        tasks = [{"id": "x", "cpu_request": 10.0, "memory_request": 10.0}]
        allocations, _, _ = allocate_greedy(tasks, servers)
        self.assertEqual(allocations[0]["server_id"], "S1")

    def test_backtracking_finds_feasible_exact_assignment(self):
        servers = [
            {
                "server_id": "S1",
                "cpu_capacity": 100.0,
                "memory_capacity": 100.0,
                "cpu_available": 100.0,
                "memory_available": 100.0,
            },
            {
                "server_id": "S2",
                "cpu_capacity": 100.0,
                "memory_capacity": 100.0,
                "cpu_available": 100.0,
                "memory_available": 100.0,
            },
        ]
        tasks = [
            {"id": "a", "priority_score": 9, "cpu_request": 60.0, "memory_request": 60.0},
            {"id": "b", "priority_score": 8, "cpu_request": 60.0, "memory_request": 60.0},
        ]
        allocations, unassigned, _ = allocate_backtracking(tasks, servers)
        self.assertEqual(len(allocations), 2)
        self.assertEqual(len(unassigned), 0)

    def test_branch_and_bound_returns_ranked_output(self):
        tasks = [
            {"id": "a", "priority_score": 9, "predicted_execution_time": 5},
            {"id": "b", "priority_score": 8, "predicted_execution_time": 2},
            {"id": "c", "priority_score": 3, "predicted_execution_time": 1},
        ]
        ordered = schedule_branch_and_bound(tasks)
        self.assertEqual(len(ordered), 3)
        self.assertEqual(ordered[0]["schedule_rank"], 1)
        self.assertEqual(ordered[-1]["schedule_rank"], 3)

    def test_dynamic_programming_knapsack_style_scheduler(self):
        tasks = [
            {"id": "a", "cpu_request": 10, "priority_score": 10},
            {"id": "b", "cpu_request": 20, "priority_score": 8},
            {"id": "c", "cpu_request": 100, "priority_score": 1},
        ]
        ordered = schedule_dp(tasks)
        self.assertEqual(len(ordered), 3)
        self.assertEqual(ordered[0]["schedule_rank"], 1)
        self.assertEqual(ordered[-1]["schedule_rank"], 3)


if __name__ == "__main__":
    unittest.main()
