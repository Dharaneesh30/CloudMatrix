import { useEffect, useState } from "react";

import { fetchServerBalance, rebalanceUnassigned } from "../services/api";

export default function LoadBalancePage() {
  const [data, setData] = useState({ servers: [], remaining_unassigned: 0 });
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await fetchServerBalance();
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load server balance");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onRebalance = async () => {
    try {
      setBusy(true);
      setError("");
      setMessage("");
      const res = await rebalanceUnassigned(true, 200000, 25000);
      const processedRows = Number(res.processed_rows || 0);
      setMessage(
        `${res.message}. Rebalanced: ${res.rebalanced}, Remaining: ${res.remaining_unassigned}, New Servers: ${res.new_servers}, Processed Rows: ${processedRows}${res.partial ? " (more batches needed)" : ""}`
      );
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Rebalance failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-semibold">Step 5: Load Balance</h2>
        <p className="mt-1 text-sm text-ink/65">
          Balance remaining unassigned tasks across current and auto-scaled servers.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            onClick={onRebalance}
            disabled={busy}
            className="rounded-xl bg-gradient-to-r from-ember to-orange-400 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Balancing..." : "Rebalance Unassigned Tasks"}
          </button>
          <button
            onClick={load}
            disabled={loading}
            className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-ink"
          >
            Refresh
          </button>
          <span className="text-sm text-ink/70">Remaining unassigned: {data.remaining_unassigned}</span>
        </div>

        {message && <p className="mt-3 text-sm font-medium text-mint">{message}</p>}
        {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
      </div>

      <div className="glass-card p-4">
        <h3 className="mb-3 font-display text-lg font-semibold">Server Utilization</h3>
        <div className="overflow-auto rounded-xl border border-ink/10 bg-white/80">
          <table className="min-w-[980px] w-full text-sm">
            <thead className="bg-dawn/90 text-left font-display text-xs uppercase tracking-wide text-ink/65">
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
                <tr key={server.server_id} className="border-t border-ink/10 hover:bg-white">
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
    </section>
  );
}
