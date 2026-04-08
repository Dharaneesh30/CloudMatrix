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

  const [algorithm] = useState("sjf");
  const [result, setResult] = useState(cached?.result || { page: { tasks: [] }, result: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(cached?.error || "");
  const { isProcessing, isCompleted, hasRun, dataVersion, notifyDataChanged } = usePipeline();

  const locked = isProcessing || !hasRun;

  const onRun = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await runSchedule(algorithm, 1, 50);
      setResult(res);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem("cm_scheduling_cache", JSON.stringify({ result: res, error: "" }));
      }
      notifyDataChanged();
    } catch (err) {
      const message = err?.response?.data?.detail || "Scheduling update failed";
      setError(message);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem("cm_scheduling_cache", JSON.stringify({ result, error: message }));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!hasRun) return;
    fetchTasks(1, 50)
      .then((res) =>
        setResult((prev) => {
          const next = { ...prev, page: res };
          if (typeof window !== "undefined") {
            window.sessionStorage.setItem("cm_scheduling_cache", JSON.stringify({ result: next, error }));
          }
          return next;
        })
      )
      .catch(() => {
        // keep existing result on transient errors
      });
  }, [hasRun, dataVersion, error]);

  return (
    <section className="space-y-4">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-xl font-semibold">Step 3: Scheduling Strategy</h2>
        <p className="mt-1 text-sm text-ink/65">
          This page applies a single scheduling concept: Shortest Job First (SJF).
        </p>
        <p className="mt-1 text-sm text-ink/55">
          Tasks with shorter execution time are scheduled first for better throughput.
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
            Scheduling: SJF
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
