# CloudMatrix Algorithm Concept Coverage

This project keeps the Scheduling page fixed (SJF in UI), while implementing and using all required algorithmic concepts in backend flow.

## 1) Divide and Conquer
- Implementation:
  - `backend/core/merge_sort.py`
- Technique used:
  - Recursive stable merge sort (`split -> solve halves -> merge`).
- Where used:
  - `backend/core/stage_preprocessing.py` (Stage 3 prioritization).
  - `backend/core/scheduling_engine.py` (greedy/backtracking ordering).
- Why:
  - Deterministic, stable priority ordering for large task lists.

## 2) Greedy Method
- Implementation:
  - `backend/core/greedy_allocator.py`
- Technique used:
  - Best-fit least-loaded server selection among feasible servers.
- Where used:
  - `backend/core/scheduling_engine.py` as default allocator and large-input fallback.
  - `backend/core/pipeline.py` via `allocate_for_schedule(...)`.
- Why:
  - Fast near-optimal allocation for throughput and load balancing.

## 3) Dynamic Programming
- Implementation:
  - `backend/core/dp_scheduler.py`
- Technique used:
  - Knapsack-style DP table over weighted CPU budget.
  - Reconstruct selected high-value subset, append tail by greedy order.
- Where used:
  - `backend/core/scheduling_engine.py` when schedule type resolves to `dp`.
- Why:
  - Better value-aware ordering when resource constraints matter.

## 4) Hashing
- Implementation:
  - `backend/core/hash_table.py` (chaining + resize)
  - `backend/core/task_cache.py` (thread-safe cache wrapper)
- Technique used:
  - O(1)-average insert/get/delete on task id keys.
- Where used:
  - `backend/core/stage_preprocessing.py` Stage 1.
  - `backend/api/routes_fastapi.py` task read hot path (`/task/{task_id}`).
- Why:
  - Low-latency lookup and reduced repeated DB reads.

## 5) Backtracking / Branch and Bound
- Backtracking implementation:
  - `backend/core/backtracking_allocator.py`
- Technique used:
  - DFS exact search with pruning for small batches (`<= 22`).
- Where used:
  - `backend/core/scheduling_engine.py` for small workload allocation.
- Why:
  - Exact feasible assignment on small input sizes.

- Branch and Bound implementation:
  - `backend/core/branch_bound.py`
- Technique used:
  - Priority-queue search with lower-bound pruning and expansion caps.
- Where used:
  - `backend/core/scheduling_engine.py` for medium input ordering.
- Why:
  - Better-quality ordering than plain greedy while controlling runtime.

## 6) Tree Concepts
- Implementation:
  - `backend/core/tree_structure.py`
- Techniques used:
  - Server hierarchy tree construction.
  - Breadth-first traversal (level order).
  - Task priority BST insert/search/inorder.
- Where used:
  - `backend/core/pipeline.py` in `get_server_balance()` response (`server_tree`).
- Why:
  - Structured representation for server topology and educational tree operations.

## 7) Runtime Algorithm Resolution
- `backend/core/scheduling_engine.py` maps `fast` / `hybrid` into:
  - small -> `backtracking`
  - medium -> `branch_bound`
  - large -> `greedy`

This keeps UI simple/fixed while still demonstrating multiple advanced algorithmic techniques in backend execution.
