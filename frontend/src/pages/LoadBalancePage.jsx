import { useCallback, useEffect, useState } from "react";

import { usePipeline } from "../context/usePipeline";
import { fetchServerBalance, fetchUnassignedTasks, rebalanceUnassigned } from "../services/api";

export default function LoadBalancePage() {
  const cachedRaw =
    typeof window !== "undefined" ? window.sessionStorage.getItem("cm_balance_cache") : null;
  let cached = null;
  try {
    cached = cachedRaw ? JSON.parse(cachedRaw) : null;
  } catch {
    cached = null;
  }

  const [data, setData] = useState(cached?.data || { servers: [], remaining_unassigned: 0 });
  const [unassigned, setUnassigned] = useState(
    cached?.unassigned || { page: 1, limit: 20, total: null, has_more: false, tasks: [] }
  );
  const [unassignedPage, setUnassignedPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(cached?.message || "");
  const [error, setError] = useState(cached?.error || "");
  const [queueWarning, setQueueWarning] = useState("");
  const { hasRun, dataVersion, notifyDataChanged } = usePipeline();

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const loadUnassignedWithRetry = useCallback(
    async (page, limit, includeTotal) => {
      let lastError = null;
      for (let attempt = 0; attempt < 4; attempt += 1) {
        try {
          return await fetchUnassignedTasks(page, limit, includeTotal);
        } catch (err) {
          lastError = err;
          await sleep(200 + attempt * 250);
        }
      }
      throw lastError || new Error("Failed to load unassigned queue");
    },
    []
  );

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      setQueueWarning("");
      const [balanceResult, unassignedResult] = await Promise.allSettled([
        fetchServerBalance(),
        loadUnassignedWithRetry(unassignedPage, 20, unassignedPage === 1),
      ]);

      if (balanceResult.status !== "fulfilled") {
        const msg = balanceResult.reason?.response?.data?.detail || "Failed to load server balance";
        throw new Error(msg);
      }

      const balanceRes = balanceResult.value;
      const unassignedRes =
        unassignedResult.status === "fulfilled"
          ? unassignedResult.value
          : null;

      if (unassignedResult.status !== "fulfilled" && Number(balanceRes?.remaining_unassigned || 0) > 0) {
        const statusCode = unassignedResult.reason?.response?.status;
        if (statusCode === 404) {
          setQueueWarning("Unassigned queue endpoint not found. Restart backend on :8000 to load latest API routes.");
        } else {
          setQueueWarning("Unassigned queue is temporarily busy. Retrying automatically.");
        }
      }

      setData(balanceRes);
      if (unassignedRes) {
        setUnassigned(unassignedRes);
      }
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_balance_cache",
          JSON.stringify({ data: balanceRes, unassigned: unassignedRes || unassigned, message: "", error: "" })
        );
      }
    } catch (err) {
      const msg = err?.message || err?.response?.data?.detail || "Failed to load server balance";
      setError(msg);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_balance_cache",
          JSON.stringify({
            data: { servers: [], remaining_unassigned: 0 },
            unassigned: { page: 1, limit: 20, total: null, has_more: false, tasks: [] },
            message: "",
            error: msg,
          })
        );
      }
    } finally {
      setLoading(false);
    }
  }, [unassignedPage, loadUnassignedWithRetry]);

  useEffect(() => {
    if (!hasRun) return;
    load();
  }, [hasRun, dataVersion, load]);

  const onRebalance = async () => {
    try {
      setBusy(true);
      setError("");
      setMessage("");
      // Smaller batches keep UI responsive; users can run multiple rounds.
      const res = await rebalanceUnassigned(true, 50000, 10000);
      const processedRows = Number(res.processed_rows || 0);
      notifyDataChanged();
      const msg =
        `${res.message}. Rebalanced: ${res.rebalanced}, Remaining: ${res.remaining_unassigned}, New Servers: ${res.new_servers}, Processed Rows: ${processedRows}${res.partial ? " (more batches needed)" : ""}`
      setMessage(msg);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_balance_cache",
          JSON.stringify({ data, unassigned, message: msg, error: "" })
        );
      }
      await load();
    } catch (err) {
      const msg = err?.response?.data?.detail || "Rebalance failed";
      setError(msg);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_balance_cache",
          JSON.stringify({ data, unassigned, message, error: msg })
        );
      }
    } finally {
      setBusy(false);
    }
  };

  const unassignedPages =
    Number.isFinite(Number(unassigned?.total))
      ? Math.max(1, Math.ceil(Number(unassigned?.total || 0) / 20))
      : null;

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-xl font-semibold">Step 4: Allocation</h2>
        <p className="mt-1 text-sm text-ink/65">
          Allocate unassigned tasks to least-loaded feasible servers with auto-scale fallback.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            onClick={onRebalance}
            disabled={busy}
            className="btn-primary"
          >
            {busy ? "Balancing..." : "Rebalance Unassigned Tasks"}
          </button>
          <button
            onClick={load}
            disabled={loading}
            className="btn-secondary"
          >
            Refresh
          </button>
          <span className="text-sm text-ink/70">Remaining unassigned: {data.remaining_unassigned}</span>
        </div>

        {message && <p className="mt-3 text-sm font-medium text-mint">{message}</p>}
        {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
        {queueWarning && <p className="mt-3 text-sm font-medium text-amber-700">{queueWarning}</p>}
      </div>

      <div className="glass-card p-4 md:p-5">
        <h3 className="mb-3 font-display text-lg font-semibold">Server Utilization</h3>
        <div className="table-shell">
          <table className="min-w-[980px] w-full text-sm">
            <thead className="table-head text-left font-display text-xs uppercase tracking-wide text-ink/65">
              <tr>
                <th className="px-3 py-2">Server</th>
                <th className="px-3 py-2">Tasks</th>
                <th className="px-3 py-2">CPU Used</th>
                <th className="px-3 py-2">CPU Capacity</th>
                <th className="px-3 py-2">CPU Util %</th>
                <th className="px-3 py-2">Memory Used</th>
                <th className="px-3 py-2">Memory Capacity</th>
                <th className="px-3 py-2">Memory Util %</th>
                <th className="px-3 py-2">Avg Pred Load</th>
              </tr>
            </thead>
            <tbody>
              {data.servers.map((server) => (
                <tr key={server.server_id} className="table-row border-t border-ink/10">
                  <td className="px-3 py-2 font-medium">{server.server_id}</td>
                  <td className="px-3 py-2">{server.task_count}</td>
                  <td className="px-3 py-2">{Number(server.cpu_used).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(server.cpu_capacity).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(server.cpu_utilization_pct).toFixed(2)}%</td>
                  <td className="px-3 py-2">{Number(server.memory_used).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(server.memory_capacity).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(server.memory_utilization_pct).toFixed(2)}%</td>
                  <td className="px-3 py-2">{Number(server.avg_predicted_load).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-card p-4 md:p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-display text-lg font-semibold">Unassigned Tasks Queue</h3>
          <span className="text-sm text-ink/70">
            Page {unassigned.page || 1}
            {unassignedPages ? ` / ${unassignedPages}` : ""}
            {" | "}
            Total: {Number.isFinite(Number(unassigned.total)) ? unassigned.total : "fast mode"}
          </span>
        </div>

        <div className="table-shell">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="table-head text-left font-display text-xs uppercase tracking-wide text-ink/65">
              <tr>
                <th className="px-3 py-2">Task ID</th>
                <th className="px-3 py-2">Priority</th>
                <th className="px-3 py-2">Priority Score</th>
                <th className="px-3 py-2">CPU</th>
                <th className="px-3 py-2">Memory</th>
                <th className="px-3 py-2">Predicted Time</th>
                <th className="px-3 py-2">Algo</th>
              </tr>
            </thead>
            <tbody>
              {(unassigned.tasks || []).map((task) => (
                <tr key={task.id} className="table-row border-t border-ink/10">
                  <td className="px-3 py-2 font-medium">{task.id}</td>
                  <td className="px-3 py-2">{Number(task.priority || 0).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(task.priority_score || 0).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(task.cpu_request || 0).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(task.memory_request || 0).toFixed(2)}</td>
                  <td className="px-3 py-2">{Number(task.predicted_execution_time || 0).toFixed(2)}</td>
                  <td className="px-3 py-2">{task.scheduling_type || "-"}</td>
                </tr>
              ))}
              {(!unassigned.tasks || unassigned.tasks.length === 0) && (
                <tr className="border-t border-ink/10">
                  <td className="px-3 py-3 text-ink/65" colSpan={7}>
                    {Number(data?.remaining_unassigned || 0) > 0
                      ? "Queue is loading or temporarily unavailable. Click Refresh."
                      : "No unassigned tasks in current view."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

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
              setUnassignedPage((p) =>
                unassignedPages ? Math.min(unassignedPages, p + 1) : p + 1
              )
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
