# CloudMatrix Algorithm Concept Coverage

## CAT Internal Marks Evaluation (Total: 60)

1. 2026-03-18: Divide and Conquer + Greedy Method Implementation (20 marks)
2. 2026-04-01: Dynamic Programming (10 marks)
3. 2026-04-10: Hashing + Backtracking / Branch and Bound + Tree Algorithms (30 marks)

## Concept-to-Implementation Map

| Concept | Algorithms Used | Time Complexity | Space Complexity | Primary Modules |
|---|---|---|---|---|
| Divide and Conquer | Stable Merge Sort | O(n log n) | O(n) | `backend/core/merge_sort.py`, `backend/core/stage_preprocessing.py` |
| Greedy Method | Best-Fit Decreasing Resource Allocation | O(T log T + T*S) | O(T + S) | `backend/core/greedy_allocator.py`, `backend/core/scheduling_engine.py` |
| Dynamic Programming | Knapsack-style DP Scheduler | O(N*C) | O(N*C) | `backend/core/dp_scheduler.py` |
| Hashing | Chained Hash Table + Task Cache | O(1) avg, O(n) worst | O(n) | `backend/core/hash_table.py`, `backend/core/task_cache.py` |
| Backtracking | Exact bounded DFS allocation | O(S^T) worst | O(T) | `backend/core/backtracking_allocator.py` |
| Branch and Bound | Priority-queue bounded search with pruning | Exponential worst-case (bounded expansions) | O(K) | `backend/core/branch_bound.py` |
| Tree Algorithms | Server hierarchy tree + BFS, Priority BST | O(V+E), O(h) insert/search, O(n) traversal | O(V), O(n) | `backend/core/tree_structure.py`, `backend/core/pipeline.py` |

Legend:
- `T` = number of tasks
- `S` = number of servers
- `N` = DP candidate tasks
- `C` = DP capacity units
- `K` = active branch-and-bound frontier
- `V`, `E` = tree nodes and edges
- `h` = BST height

## Efficient Runtime Strategy

`backend/core/scheduling_engine.py` uses adaptive selection for `fast` / `hybrid`:

1. Small datasets: `backtracking` for exactness
2. Medium datasets: `branch_bound` for quality with bounded search
3. Large datasets: `greedy` for throughput and scalability

This ensures all required concepts are implemented and demonstrable while maintaining practical runtime and memory behavior.
