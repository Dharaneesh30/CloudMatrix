export default function ProgressStatus({ status }) {
  const progress = Math.max(0, Math.min(100, Number(status?.progress || 0)));
  const state = status?.status || "idle";

  return (
    <div className="glass-card p-4">
      <div className="mb-2 flex items-center justify-between text-sm font-medium">
        <span className="capitalize text-ink/70">{state}</span>
        <span>{progress}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-ink/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-ember to-mint transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-2 text-sm text-ink/70">{status?.message || "Waiting for dataset upload"}</p>
      {!!status?.error && <p className="mt-1 text-sm font-medium text-red-600">{status.error}</p>}
    </div>
  );
}
