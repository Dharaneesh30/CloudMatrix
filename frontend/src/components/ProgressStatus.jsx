export default function ProgressStatus({ status }) {
  const progress = Math.max(0, Math.min(100, Number(status?.progress || 0)));
  const state = status?.status || "idle";
  const stateTone =
    state === "completed"
      ? "bg-mint/20 text-mint"
      : state === "processing" || state === "queued"
      ? "bg-sky-100 text-sky-700"
      : "bg-ink/10 text-ink/70";

  return (
    <div className="glass-card p-4 md:p-5">
      <div className="mb-2 flex items-center justify-between text-sm font-medium">
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${stateTone}`}>{state}</span>
        <span className="font-semibold text-ink">{progress}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-ink/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-ember to-mint transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-2 text-sm text-ink/70">{status?.message || "Waiting for dataset upload"}</p>
      {!!status?.error && <p className="mt-1 text-sm font-medium text-red-600">{status.error}</p>}
    </div>
  );
}
