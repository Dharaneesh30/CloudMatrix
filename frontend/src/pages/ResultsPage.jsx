import { useCallback, useEffect, useState } from "react";

import TasksTable from "../components/TasksTable";
import { usePipeline } from "../context/usePipeline";
import { fetchMetrics, fetchServerBalance, fetchTaskById, fetchTasks } from "../services/api";

function SummaryCard({ title, value }) {
  return (
    <div className="metric-card">
      <p className="text-xs uppercase tracking-wide text-ink/55">{title}</p>
      <p className="mt-1 font-display text-xl font-semibold">{value}</p>
    </div>
  );
}

export default function ResultsPage() {
  const cached =
    typeof window !== "undefined" ? window.sessionStorage.getItem("cm_results_cache") : null;
  const parsedCache = cached ? JSON.parse(cached) : null;
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(50);
  const [data, setData] = useState(parsedCache?.data || { tasks: [], total: 0, page: 1, limit: 50 });
  const [metrics, setMetrics] = useState(parsedCache?.metrics || null);
  const [serverBalance, setServerBalance] = useState(parsedCache?.serverBalance || null);
  const [searchId, setSearchId] = useState("");
  const [searchResult, setSearchResult] = useState(null);
  const [error, setError] = useState("");
  const { status, isProcessing, hasRun, dataVersion } = usePipeline();

  const load = useCallback(async (targetPage = page, targetLimit = limit) => {
    try {
      setError("");
      const [tasksRes, metricsRes, balanceRes] = await Promise.all([
        fetchTasks(targetPage, targetLimit),
        fetchMetrics("lite"),
        fetchServerBalance(),
      ]);
      setData(tasksRes);
      setMetrics(metricsRes);
      setServerBalance(balanceRes);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_results_cache",
          JSON.stringify({
            data: tasksRes,
            metrics: metricsRes,
            serverBalance: balanceRes,
          })
        );
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to refresh results (showing last loaded data)");
    }
  }, [page, limit]);

  useEffect(() => {
    if (!hasRun) return;
    const kickoff = setTimeout(() => {
      void load(page, limit);
    }, 0);
    const timer = setInterval(() => {
      void load(page, limit);
    }, isProcessing ? 4000 : 12000);
    return () => {
      clearTimeout(kickoff);
      clearInterval(timer);
    };
  }, [page, limit, hasRun, dataVersion, load, isProcessing]);

  const totalPages = Math.max(1, Math.ceil((data.total || 0) / limit));
  const unassigned = Number(serverBalance?.remaining_unassigned || 0);
  const assigned = Math.max(0, Number(data.total || metrics?.total_tasks || 0) - unassigned);

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
      <section className="glass-card p-5 md:p-6">
        <h2 className="font-display text-xl font-semibold">Step 5: Results</h2>
        <p className="mt-2 text-sm text-ink/65">Upload a dataset first to unlock results.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="font-display text-xl font-semibold">Step 5: Results</h2>
            <p className="text-sm text-ink/65">End-to-end output of upload, scheduling, allocation, and balancing.</p>
            {isProcessing && (
              <p className="mt-2 text-sm text-sky-700">Processing is running. You are viewing partial results until completion.</p>
            )}
          </div>

          <div className="flex gap-2">
            <input
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="Find task by id"
              className="input-modern"
            />
            <button onClick={onSearch} className="btn-primary px-4">
              Search
            </button>
          </div>
        </div>

        {searchResult && (
          <div className="mt-4 rounded-xl border border-mint/35 bg-mint/10 p-3 text-sm">
            <strong>Task {searchResult.id}</strong> | Rank: {searchResult.schedule_rank} | Server:{" "}
            {searchResult.allocated_server || "unassigned"} | Allocated:{" "}
            {Number(searchResult.allocation_success || 0) === 1 ? "yes" : "no"}
          </div>
        )}

        {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard title="Pipeline Status" value={String(status?.status || "idle")} />
          <SummaryCard title="Total Tasks" value={Number(data.total || metrics?.total_tasks || 0)} />
          <SummaryCard title="Assigned Tasks" value={assigned} />
          <SummaryCard title="Unassigned Tasks" value={unassigned} />
          <SummaryCard title="Avg Execution" value={Number(metrics?.avg_execution_time || 0).toFixed(2)} />
          <SummaryCard title="Avg Predicted Time" value={Number(metrics?.avg_predicted_execution_time || 0).toFixed(2)} />
          <SummaryCard title="Active Servers" value={Number(metrics?.active_servers || 0)} />
          <SummaryCard
            title="Latest Run"
            value={metrics?.recent_run?.schedule_type ? String(metrics.recent_run.schedule_type).toUpperCase() : "N/A"}
          />
        </div>
      </div>

      <div className="glass-card p-4 md:p-5">
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
            className="input-modern w-auto px-2 py-1"
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
            className="btn-secondary rounded-lg px-3 py-1.5"
          >
            Prev
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="btn-secondary rounded-lg px-3 py-1.5"
          >
            Next
          </button>
        </div>

        <TasksTable tasks={data.tasks} />
      </div>
    </section>
  );
}
