import { useCallback, useEffect, useState } from "react";

import MetricsCharts from "../components/MetricsCharts";
import ProgressStatus from "../components/ProgressStatus";
import { usePipeline } from "../context/usePipeline";
import { fetchMetrics } from "../services/api";

function StatCard({ title, value }) {
  return (
    <div className="metric-card">
      <p className="text-xs uppercase tracking-wider text-ink/55">{title}</p>
      <p className="mt-2 font-display text-2xl font-semibold">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const { status } = usePipeline();

  const load = useCallback(async () => {
    try {
      setError("");
      const res = await fetchMetrics();
      setMetrics(res);
    } catch (err) {
      if (err?.code === "ECONNABORTED") {
        setError("Metrics request timed out. Backend is busy; retrying shortly.");
        return;
      }
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load metrics"
      );
    }
  }, []);

  useEffect(() => {
    const kickoff = setTimeout(() => {
      void load();
    }, 0);
    const timer = setInterval(load, 4000);
    return () => {
      clearTimeout(kickoff);
      clearInterval(timer);
    };
  }, [load]);

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-2xl font-semibold">Step 2: Monitor Pipeline</h2>
        <p className="text-sm text-ink/65">Track progress here while backend processing continues in background.</p>
      </div>

      {error && <p className="text-sm font-medium text-red-600">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total Tasks" value={metrics?.total_tasks ?? 0} />
        <StatCard title="Avg Execution" value={Number(metrics?.avg_execution_time || 0).toFixed(2)} />
        <StatCard title="Active Servers" value={metrics?.active_servers ?? 0} />
        <StatCard title="Avg Predicted Load" value={Number(metrics?.avg_predicted_server_load || 0).toFixed(2)} />
      </div>

      <ProgressStatus status={status} />

      <MetricsCharts
        priorityData={metrics?.priority_distribution || []}
        serverLoadData={metrics?.server_load_distribution || []}
      />
    </section>
  );
}
