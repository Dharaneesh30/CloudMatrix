import { useCallback, useEffect, useRef, useState } from "react";

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
  const [isRetrying, setIsRetrying] = useState(false);
  const { status } = usePipeline();
  const failureCountRef = useRef(0);
  const inFlightRef = useRef(false);
  const retryTimerRef = useRef(null);

  const load = useCallback(async (preferredMode) => {
    if (inFlightRef.current) {
      return;
    }

    const phase = String(status?.status || "idle");
    const mode = preferredMode || (phase === "queued" || phase === "processing" ? "auto" : "full");
    inFlightRef.current = true;
    try {
      const res = await fetchMetrics(mode);
      setMetrics(res);
      failureCountRef.current = 0;
      setError("");
    } catch (err) {
      failureCountRef.current += 1;
      if (err?.code === "ECONNABORTED") {
        setError("Metrics request timed out. Backend is busy; retrying shortly.");

        if (retryTimerRef.current) {
          clearTimeout(retryTimerRef.current);
        }

        retryTimerRef.current = setTimeout(() => {
          retryTimerRef.current = null;
          void load("lite");
        }, 1500);
        return;
      }
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load metrics"
      );
    } finally {
      inFlightRef.current = false;
    }
  }, [status?.status]);

  const onRetry = useCallback(async () => {
    setIsRetrying(true);
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }

    try {
      await load("lite");
    } finally {
      setIsRetrying(false);
    }
  }, [load]);

  useEffect(() => {
    const phase = String(status?.status || "idle");
    const pollMs = phase === "queued" || phase === "processing" ? 3000 : 6000;
    const kickoff = setTimeout(() => {
      void load();
    }, 0);
    const timer = setInterval(() => {
      void load();
    }, pollMs);
    return () => {
      clearTimeout(kickoff);
      clearInterval(timer);
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
    };
  }, [load, status?.status]);

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-2xl font-semibold">Step 2: Monitor Pipeline</h2>
        <p className="text-sm text-ink/65">Track progress here while backend processing continues in background.</p>
      </div>

      {error && (
        <div className="flex flex-col gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 md:flex-row md:items-center md:justify-between">
          <p className="font-medium">{error}</p>
          <button
            type="button"
            onClick={() => void onRetry()}
            disabled={isRetrying || inFlightRef.current}
            className="inline-flex items-center justify-center rounded-full border border-red-300 bg-white px-4 py-2 font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isRetrying || inFlightRef.current ? "Retrying..." : "Retry now"}
          </button>
        </div>
      )}

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
