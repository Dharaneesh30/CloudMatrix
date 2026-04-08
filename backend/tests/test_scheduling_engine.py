import unittest

from backend.core.scheduling_engine import resolve_schedule_type, schedule_tasks


class SchedulingEngineTests(unittest.TestCase):
    def test_fast_resolves_to_heap(self):
        self.assertEqual(resolve_schedule_type("fast", 10), "backtracking")
        self.assertEqual(resolve_schedule_type("fast", 500), "branch_bound")
        self.assertEqual(resolve_schedule_type("fast", 100000), "greedy")

    def test_sjf_sorts_by_predicted_time_then_priority(self):
        tasks = [
            {"id": "t3", "predicted_execution_time": 8, "priority": 2},
            {"id": "t1", "predicted_execution_time": 3, "priority": 4},
            {"id": "t2", "predicted_execution_time": 3, "priority": 6},
        ]

        ordered = schedule_tasks(tasks, "sjf")
        ids = [task["id"] for task in ordered]

        self.assertEqual(ids, ["t2", "t1", "t3"])
        self.assertEqual(ordered[0]["schedule_rank"], 1)
        self.assertEqual(ordered[-1]["schedule_rank"], 3)

    def test_dp_scheduler_produces_ranked_output(self):
        tasks = [
            {"id": "a", "cpu_request": 10, "priority_score": 9.0},
            {"id": "b", "cpu_request": 15, "priority_score": 8.0},
            {"id": "c", "cpu_request": 90, "priority_score": 2.0},
        ]
        ordered = schedule_tasks(tasks, "dp")
        self.assertEqual(len(ordered), 3)
        self.assertEqual(ordered[0]["schedule_rank"], 1)
        self.assertEqual(ordered[-1]["schedule_rank"], 3)


if __name__ == "__main__":
    unittest.main()
