from __future__ import annotations

from typing import Dict, List


def build_algorithm_catalog() -> List[Dict]:
    """
    Canonical concept coverage map used by docs/API/UI.
    Complexity is expressed with typical-case bounds for current implementations.
    """
    return [
        {
            "concept": "Divide and Conquer",
            "evaluation_date": "2026-03-18",
            "weight_marks": 20,
            "algorithms": [
                {
                    "name": "Merge Sort (stable)",
                    "module": "backend/core/merge_sort.py",
                    "used_in": [
                        "backend/core/stage_preprocessing.py",
                        "backend/core/scheduling_engine.py",
                    ],
                    "time_complexity": "O(n log n)",
                    "space_complexity": "O(n)",
                    "notes": "Deterministic ordering for priority-heavy ranking.",
                }
            ],
        },
        {
            "concept": "Greedy Method",
            "evaluation_date": "2026-03-18",
            "weight_marks": 20,
            "algorithms": [
                {
                    "name": "Best-Fit Decreasing Allocation",
                    "module": "backend/core/greedy_allocator.py",
                    "used_in": [
                        "backend/core/scheduling_engine.py",
                        "backend/core/pipeline.py",
                    ],
                    "time_complexity": "O(T log T + T*S)",
                    "space_complexity": "O(T + S)",
                    "notes": "T=tasks, S=servers; optimized for large workloads.",
                }
            ],
        },
        {
            "concept": "Dynamic Programming",
            "evaluation_date": "2026-04-01",
            "weight_marks": 10,
            "algorithms": [
                {
                    "name": "Knapsack-Style Task Scheduler",
                    "module": "backend/core/dp_scheduler.py",
                    "used_in": ["backend/core/scheduling_engine.py"],
                    "time_complexity": "O(N*C)",
                    "space_complexity": "O(N*C)",
                    "notes": "N=candidate tasks, C=capacity units; bounded candidate set for responsiveness.",
                }
            ],
        },
        {
            "concept": "Hashing",
            "evaluation_date": "2026-04-10",
            "weight_marks": 30,
            "algorithms": [
                {
                    "name": "Hash Table with Chaining + Resize",
                    "module": "backend/core/hash_table.py",
                    "used_in": [
                        "backend/core/stage_preprocessing.py",
                        "backend/core/task_cache.py",
                        "backend/api/routes_fastapi.py",
                    ],
                    "time_complexity": "O(1) average, O(n) worst-case",
                    "space_complexity": "O(n)",
                    "notes": "Fast task-id lookup for hot paths.",
                }
            ],
        },
        {
            "concept": "Backtracking",
            "evaluation_date": "2026-04-10",
            "weight_marks": 30,
            "algorithms": [
                {
                    "name": "Exact Resource Allocation (bounded search)",
                    "module": "backend/core/backtracking_allocator.py",
                    "used_in": ["backend/core/scheduling_engine.py"],
                    "time_complexity": "O(S^T) worst-case",
                    "space_complexity": "O(T)",
                    "notes": "Used only for small inputs for exactness.",
                }
            ],
        },
        {
            "concept": "Branch and Bound",
            "evaluation_date": "2026-04-10",
            "weight_marks": 30,
            "algorithms": [
                {
                    "name": "Bounded Priority-Queue Search",
                    "module": "backend/core/branch_bound.py",
                    "used_in": ["backend/core/scheduling_engine.py"],
                    "time_complexity": "Exponential worst-case, bounded by expansion cap",
                    "space_complexity": "O(K)",
                    "notes": "K is active search frontier; used for medium-sized datasets.",
                }
            ],
        },
        {
            "concept": "Tree Algorithms",
            "evaluation_date": "2026-04-10",
            "weight_marks": 30,
            "algorithms": [
                {
                    "name": "Server Hierarchy Tree + BFS",
                    "module": "backend/core/tree_structure.py",
                    "used_in": ["backend/core/pipeline.py"],
                    "time_complexity": "O(V + E)",
                    "space_complexity": "O(V)",
                    "notes": "Level-order traversal for server topology view.",
                },
                {
                    "name": "Task Priority Binary Search Tree",
                    "module": "backend/core/tree_structure.py",
                    "used_in": ["backend/tests/test_tree_structure.py"],
                    "time_complexity": "Insert/Search O(h), Inorder O(n)",
                    "space_complexity": "O(n)",
                    "notes": "Educational BST operations over priority scores.",
                },
            ],
        },
    ]


def summarize_evaluation_scheme() -> Dict:
    return {
        "total_marks": 60,
        "evaluations": [
            {
                "date": "2026-03-18",
                "focus": "Divide and Conquer, Greedy Method Implementation",
                "marks": 20,
            },
            {
                "date": "2026-04-01",
                "focus": "Dynamic Programming",
                "marks": 10,
            },
            {
                "date": "2026-04-10",
                "focus": "Hashing, Backtracking / Branch and Bound, Tree Algorithms (BFS, BST)",
                "marks": 30,
            },
        ],
    }
