import { useState } from "react";

import TasksTable from "../components/TasksTable";
import { usePipeline } from "../context/PipelineContext";
import { runSchedule } from "../services/api";

const ALGORITHMS = [
  { value: "fast", label: "fast (recommended)" },
  { value: "heap", label: "heap" },
  { value: "greedy", label: "greedy" },
  { value: "dp", label: "dp" },
  { value: "backtracking", label: "backtracking" },
  { value: "branch_bound", label: "branch_bound" },
  { value: "graph", label: "graph" },
];

export default function SchedulingPage() {
  const [algorithm, setAlgorithm] = useState("fast");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { isProcessing, isCompleted, hasRun } = usePipeline();

  const locked = isProcessing || !hasRun;

  const onRun = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await runSchedule(algorithm, 1, 50);
      setResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || "Scheduling update failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-4">
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-semibold">Step 3: Scheduling Strategy</h2>
        <p className="mt-1 text-sm text-ink/65">
          This page only handles scheduling concept. Upload is separate in Step 1.
        </p>
        <p className="mt-1 text-sm text-ink/55">
          Fast mode automatically chooses the quickest practical strategy for large datasets.
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
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value)}
            className="w-full rounded-xl border border-ink/15 bg-white px-3 py-2 sm:max-w-xs"
            disabled={locked || loading}
          >
            {ALGORITHMS.map((algo) => (
              <option key={algo.value} value={algo.value}>
                {algo.label}
              </option>
            ))}
          </select>

          <button
            onClick={onRun}
            disabled={loading || locked}
            className="rounded-xl bg-gradient-to-r from-ember to-orange-400 px-5 py-2.5 font-semibold text-white disabled:opacity-50"
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

      <div className="glass-card p-4">
        <h3 className="mb-3 font-display text-lg font-semibold">Preview (First Page)</h3>
        <TasksTable tasks={result?.page?.tasks || []} />
      </div>
    </section>
  );
}
