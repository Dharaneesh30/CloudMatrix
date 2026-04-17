# CloudMatrix AI

CloudMatrix AI is a full-stack scheduling and server-allocation system for CSV task datasets.

## Stack

- Backend: FastAPI + SQLite + pandas + scikit-learn
- Frontend: React + Vite + Tailwind + Recharts

## Project Layout

- `backend/main.py`: FastAPI entrypoint
- `backend/api/routes_fastapi.py`: API routes
- `backend/core/`: scheduling, allocation, pipeline orchestration
- `frontend/src/`: React UI pages, components, and API client

## Local Run

### One Command (Frontend + Backend)

From the repository root:

```bash
bash ./run-dev.sh
```

This starts:
- Backend at `http://127.0.0.1:8000`
- Frontend at `http://localhost:5173`

### 1) Backend

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

If your venv is inside `backend/.venv`, use:

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 2) Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend default URL is `http://localhost:5173` and backend API target is `http://localhost:8000`.

## Quality Checks

```powershell
cd frontend
npm run lint
npm run build
```

```powershell
cd ..
python -m compileall backend
```

## Main API Routes

- `GET /health`
- `POST /upload-dataset` (multipart file + `unused_servers`)
- `GET /status`
- `GET /concepts-coverage` (CAT concept mapping + time/space complexity summary)
- `GET /tasks?page=&limit=`
- `GET /task/{task_id}`
- `POST /schedule/{schedule_type}`
- `GET /metrics`
- `GET /server-balance`
- `POST /rebalance-unassigned`

## CAT Concept Coverage

CloudMatrix includes explicit implementations and usage of:
- Divide and Conquer
- Greedy
- Dynamic Programming
- Hashing
- Backtracking
- Branch and Bound
- Tree basics (hierarchy + BFS + BST operations)

See:
- `backend/docs/ALGORITHM_CONCEPT_COVERAGE.md`
- API: `GET /concepts-coverage`
- Frontend: `Step 6: Concepts`
