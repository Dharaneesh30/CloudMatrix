import { useCallback, useEffect, useMemo, useState } from "react";

import { usePipeline } from "../context/usePipeline";
import {
  fetchAssignedTasks,
  fetchUnassignedTasks,
  rebalanceUnassigned,
} from "../services/api";

const PAGE_SIZE = 20;

function TasksTable({ tasks, emptyText }) {
  return (
    <div className="table-shell">
      <table className="min-w-[980px] w-full text-sm">
        <thead className="table-head text-left font-display text-xs uppercase tracking-wide text-ink/65">
          <tr>
            <th className="px-3 py-2">Task ID</th>
            <th className="px-3 py-2">Rank</th>
            <th className="px-3 py-2">Priority</th>
            <th className="px-3 py-2">CPU</th>
            <th className="px-3 py-2">Memory</th>
            <th className="px-3 py-2">Predicted Time</th>
            <th className="px-3 py-2">Server</th>
            <th className="px-3 py-2">Algo</th>
          </tr>
        </thead>
        <tbody>
          {(tasks || []).map((task) => (
            <tr key={task.id} className="table-row border-t border-ink/10">
              <td className="px-3 py-2 font-medium">{task.id}</td>
              <td className="px-3 py-2">{Number(task.schedule_rank || 0)}</td>
              <td className="px-3 py-2">{Number(task.priority || 0).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.cpu_request || 0).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.memory_request || 0).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.predicted_execution_time || 0).toFixed(2)}</td>
              <td className="px-3 py-2">{task.allocated_server || "unassigned"}</td>
              <td className="px-3 py-2">{task.scheduling_type || "-"}</td>
            </tr>
          ))}
          {(!tasks || tasks.length === 0) && (
            <tr className="border-t border-ink/10">
              <td className="px-3 py-3 text-ink/65" colSpan={8}>
                {emptyText}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default function LoadBalancePage() {
  const cached = useMemo(() => {
    if (typeof window === "undefined") return null;
    const cachedRaw = window.sessionStorage.getItem("cm_balance_cache");
    try {
      return cachedRaw ? JSON.parse(cachedRaw) : null;
    } catch {
      return null;
    }
  }, []);

  const [assigned, setAssigned] = useState(
    cached?.assigned || { page: 1, limit: PAGE_SIZE, total: null, has_more: false, tasks: [] }
  );
  const [unassigned, setUnassigned] = useState(
    cached?.unassigned || { page: 1, limit: PAGE_SIZE, total: null, has_more: false, tasks: [] }
  );
  const [assignedPage, setAssignedPage] = useState(1);
  const [unassignedPage, setUnassignedPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(cached?.message || "");
  const [error, setError] = useState(cached?.error || "");
  const { hasRun, dataVersion, notifyDataChanged, backendReachable } = usePipeline();

  const load = useCallback(async () => {
    if (!backendReachable) {
      setError("Backend is offline. Start backend on :8000 and refresh.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const [assignedRes, unassignedRes] = await Promise.all([
        fetchAssignedTasks(assignedPage, PAGE_SIZE, assignedPage === 1),
        fetchUnassignedTasks(unassignedPage, PAGE_SIZE, unassignedPage === 1),
      ]);

      setAssigned(assignedRes);
      setUnassigned(unassignedRes);

      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_balance_cache",
          JSON.stringify({
            assigned: assignedRes,
            unassigned: unassignedRes,
            message: "",
            error: "",
            version: dataVersion,
            savedAt: Date.now(),
          })
        );
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to load allocation tables";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [assignedPage, unassignedPage, backendReachable, dataVersion]);

  useEffect(() => {
    if (!hasRun) return;
    const cacheVersion = Number(cached?.version ?? -1);
    const cacheFresh = Number(cached?.savedAt || 0) > 0 && Date.now() - Number(cached.savedAt) < 30000;
    if (
      cacheVersion === Number(dataVersion) &&
      cacheFresh &&
      ((cached?.assigned?.tasks || []).length > 0 || (cached?.unassigned?.tasks || []).length > 0)
    ) {
      return;
    }
    void load();
  }, [hasRun, dataVersion, load, cached]);

  const onRebalance = async () => {
    if (!backendReachable) {
      setError("Backend is offline. Start backend on :8000 and refresh.");
      return;
    }
    try {
      setBusy(true);
      setError("");
      setMessage("");
      const res = await rebalanceUnassigned(false, 50000, 10000);
      notifyDataChanged();
      setMessage(
        `${res.message}. Rebalanced: ${res.rebalanced}, Remaining: ${res.remaining_unassigned}, New Servers: ${res.new_servers}`
      );
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Rebalance failed");
    } finally {
      setBusy(false);
    }
  };

  const assignedPages = Number.isFinite(Number(assigned?.total))
    ? Math.max(1, Math.ceil(Number(assigned?.total || 0) / PAGE_SIZE))
    : null;
  const unassignedPages = Number.isFinite(Number(unassigned?.total))
    ? Math.max(1, Math.ceil(Number(unassigned?.total || 0) / PAGE_SIZE))
    : null;

  if (!hasRun) {
    return (
      <section className="glass-card p-5 md:p-6">
        <h2 className="font-display text-xl font-semibold">Step 4: Allocation</h2>
        <p className="mt-2 text-sm text-ink/65">Upload a dataset first to unlock allocation insights.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-xl font-semibold">Step 4: Allocation</h2>
        <p className="mt-1 text-sm text-ink/65">Split view of assigned and unassigned tasks.</p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button onClick={onRebalance} disabled={busy || !backendReachable} className="btn-primary">
            {busy ? "Balancing..." : "Rebalance Unassigned Tasks"}
          </button>
          <button onClick={load} disabled={loading || !backendReachable} className="btn-secondary">
            Refresh
          </button>
          <span className="text-sm text-ink/70">
            Assigned: {Number.isFinite(Number(assigned?.total)) ? assigned.total : "-"} | Unassigned:{" "}
            {Number.isFinite(Number(unassigned?.total)) ? unassigned.total : "-"}
          </span>
        </div>

        {message && <p className="mt-3 text-sm font-medium text-mint">{message}</p>}
        {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
      </div>

      <div className="glass-card p-4 md:p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-display text-lg font-semibold">Assigned Tasks</h3>
          <span className="text-sm text-ink/70">
            Page {assigned.page || 1}
            {assignedPages ? ` / ${assignedPages}` : ""}
          </span>
        </div>
        <TasksTable tasks={assigned.tasks} emptyText="No assigned tasks in current view." />
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setAssignedPage((p) => Math.max(1, p - 1))}
            disabled={assignedPage <= 1 || loading}
            className="btn-secondary rounded-lg px-3 py-1.5"
          >
            Prev
          </button>
          <button
            onClick={() =>
              setAssignedPage((p) => (assignedPages ? Math.min(assignedPages, p + 1) : p + 1))
            }
            disabled={(!assigned?.has_more && (!assignedPages || assignedPage >= assignedPages)) || loading}
            className="btn-secondary rounded-lg px-3 py-1.5"
          >
            Next
          </button>
        </div>
      </div>

      <div className="glass-card p-4 md:p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-display text-lg font-semibold">Unassigned Tasks</h3>
          <span className="text-sm text-ink/70">
            Page {unassigned.page || 1}
            {unassignedPages ? ` / ${unassignedPages}` : ""}
          </span>
        </div>
        <TasksTable tasks={unassigned.tasks} emptyText="No unassigned tasks in current view." />
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setUnassignedPage((p) => Math.max(1, p - 1))}
            disabled={unassignedPage <= 1 || loading}
            className="btn-secondary rounded-lg px-3 py-1.5"
          >
            Prev
          </button>
          <button
            onClick={() =>
              setUnassignedPage((p) => (unassignedPages ? Math.min(unassignedPages, p + 1) : p + 1))
            }
            disabled={(!unassigned?.has_more && (!unassignedPages || unassignedPage >= unassignedPages)) || loading}
            className="btn-secondary rounded-lg px-3 py-1.5"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
