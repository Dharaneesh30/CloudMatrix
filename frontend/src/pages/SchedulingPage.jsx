import { useEffect, useState } from "react";

import TasksTable from "../components/TasksTable";
import { usePipeline } from "../context/usePipeline";
import { fetchTasks, runSchedule } from "../services/api";

export default function SchedulingPage() {
  const cachedRaw =
    typeof window !== "undefined" ? window.sessionStorage.getItem("cm_scheduling_cache") : null;
  let cached = null;
  try {
    cached = cachedRaw ? JSON.parse(cachedRaw) : null;
  } catch {
    cached = null;
  }

  const [algorithm] = useState("fast");
  const [result, setResult] = useState(cached?.result || { page: { tasks: [] }, result: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(
    (cached?.result?.page?.tasks || []).length > 0 ? "" : (cached?.error || "")
  );
  const { isProcessing, isCompleted, hasRun, dataVersion, notifyDataChanged, backendReachable } = usePipeline();

  const locked = isProcessing || !hasRun;

  const onRun = async () => {
    if (!backendReachable) {
      setError("Backend is offline. Start backend on :8000 and try again.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await runSchedule(algorithm, 1, 50);
      setResult(res);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_scheduling_cache",
          JSON.stringify({ result: res, error: "", version: dataVersion + 1, savedAt: Date.now() })
        );
      }
      notifyDataChanged();
    } catch (err) {
      const message = err?.response?.data?.detail || "Scheduling update failed";
      setError(message);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(
          "cm_scheduling_cache",
          JSON.stringify({ result, error: message, version: dataVersion, savedAt: Date.now() })
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!hasRun) return;
    const cacheVersion = Number(cached?.version ?? -1);
    const cacheFresh = Number(cached?.savedAt || 0) > 0 && Date.now() - Number(cached.savedAt) < 30000;
    if (cacheVersion === Number(dataVersion) && cacheFresh && (cached?.result?.page?.tasks || []).length > 0) {
      // Avoid showing stale cached error when valid preview data is already present.
      setError("");
      return;
    }
    fetchTasks(1, 50)
      .then((res) => {
        setError("");
        setResult((prev) => {
          const next = { ...prev, page: res };
          if (typeof window !== "undefined") {
            window.sessionStorage.setItem(
              "cm_scheduling_cache",
              JSON.stringify({ result: next, error: "", version: dataVersion, savedAt: Date.now() })
            );
          }
          return next;
        });
      })
      .catch(() => {
        // keep existing result on transient errors
      });
  }, [hasRun, dataVersion, error, cached?.savedAt, cached?.version]);

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-xl font-semibold">Step 3: Scheduling Strategy</h2>
        <p className="mt-1 text-sm text-ink/65">
          This page applies the best available scheduler for your current dataset size.
        </p>
        <p className="mt-1 text-sm text-ink/55">
          Small datasets use deeper optimization; large datasets switch to faster ranking for quick responses.
        </p>

        {locked && (
          <p className="mt-3 rounded-xl bg-yellow-50 px-3 py-2 text-sm text-yellow-700">
            {isProcessing
              ? "Pipeline is still processing. Wait until completion before changing algorithm."
              : "Upload and process a dataset first."}
          </p>
        )}

        {!isCompleted && hasRun && !isProcessing && (
          <p className="mt-3 rounded-xl bg-sky-50 px-3 py-2 text-sm text-sky-700">
            You can still apply scheduling, but best accuracy comes after run completion.
          </p>
        )}

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <div className="w-full rounded-xl border border-ink/15 bg-white/85 px-3 py-2 text-sm font-medium sm:max-w-xs">
            Scheduling: Fast Auto Mode
          </div>

          <button
            onClick={onRun}
            disabled={loading || locked}
            className="btn-primary"
          >
            {loading ? "Applying..." : "Apply Scheduling"}
          </button>
        </div>

        {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
        {!backendReachable && (
          <p className="mt-2 text-sm font-medium text-red-600">
            Backend is unreachable. Scheduling cannot be updated right now.
          </p>
        )}
        {result?.result && (
          <p className="mt-3 text-sm text-ink/75">
            Rescheduled: <strong>{result.result.rescheduled}</strong> | Unassigned: <strong>{result.result.unassigned}</strong>
          </p>
        )}
      </div>

      <div className="glass-card p-4 md:p-5">
        <h3 className="mb-3 font-display text-lg font-semibold">Preview (First Page)</h3>
        <TasksTable tasks={result?.page?.tasks || []} />
      </div>
    </section>
  );
}
