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
- `GET /tasks?page=&limit=`
- `GET /task/{task_id}`
- `POST /schedule/{schedule_type}`
- `GET /metrics`
- `GET /server-balance`
- `POST /rebalance-unassigned`
