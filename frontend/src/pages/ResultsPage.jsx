import { useEffect, useState } from "react";

import TasksTable from "../components/TasksTable";
import { usePipeline } from "../context/PipelineContext";
import { fetchTaskById, fetchTasks } from "../services/api";

export default function ResultsPage() {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(50);
  const [data, setData] = useState({ tasks: [], total: 0, page: 1, limit: 50 });
  const [searchId, setSearchId] = useState("");
  const [searchResult, setSearchResult] = useState(null);
  const [error, setError] = useState("");
  const { isProcessing, hasRun } = usePipeline();

  const load = async (targetPage = page, targetLimit = limit) => {
    try {
      setError("");
      const res = await fetchTasks(targetPage, targetLimit);
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load tasks");
    }
  };

  useEffect(() => {
    if (!hasRun) return;
    load(page, limit);
  }, [page, limit, hasRun]);

  const totalPages = Math.max(1, Math.ceil((data.total || 0) / limit));

  const onSearch = async () => {
    if (!searchId.trim()) {
      setSearchResult(null);
      return;
    }
    try {
      setError("");
      const res = await fetchTaskById(searchId.trim());
      setSearchResult(res);
    } catch (err) {
      setSearchResult(null);
      setError(err?.response?.data?.detail || "Task not found");
    }
  };

  if (!hasRun) {
    return (
      <section className="glass-card p-5">
        <h2 className="font-display text-xl font-semibold">Step 4: Results</h2>
        <p className="mt-2 text-sm text-ink/65">Upload a dataset first to unlock results.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="glass-card p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="font-display text-xl font-semibold">Step 4: Results</h2>
            <p className="text-sm text-ink/65">Paginated table for large datasets and task-level lookup.</p>
            {isProcessing && (
              <p className="mt-2 text-sm text-sky-700">Processing is running. You are viewing partial results until completion.</p>
            )}
          </div>

          <div className="flex gap-2">
            <input
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="Find task by id"
              className="rounded-xl border border-ink/15 px-3 py-2"
            />
            <button onClick={onSearch} className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white">
              Search
            </button>
          </div>
        </div>

        {searchResult && (
          <div className="mt-4 rounded-xl border border-mint/35 bg-mint/10 p-3 text-sm">
            <strong>Task {searchResult.id}</strong> | Rank: {searchResult.schedule_rank} | Server: {searchResult.allocated_server || "unassigned"}
          </div>
        )}

        {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
      </div>

      <div className="glass-card p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-sm text-ink/70">
            Page {data.page} of {totalPages} | Total: {data.total}
          </span>

          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value));
              setPage(1);
            }}
            className="rounded-lg border border-ink/15 bg-white px-2 py-1 text-sm"
          >
            {[25, 50, 100, 200].map((v) => (
              <option key={v} value={v}>
                {v} / page
              </option>
            ))}
          </select>

          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-lg bg-white px-3 py-1.5 text-sm font-semibold disabled:opacity-50"
          >
            Prev
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="rounded-lg bg-white px-3 py-1.5 text-sm font-semibold disabled:opacity-50"
          >
            Next
          </button>
        </div>

        <TasksTable tasks={data.tasks} />
      </div>
    </section>
  );
}
