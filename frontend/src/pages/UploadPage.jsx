import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import ProgressStatus from "../components/ProgressStatus";
import { usePipeline } from "../context/PipelineContext";
import { pingHealth, uploadDataset } from "../services/api";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const { status } = usePipeline();
  const navigate = useNavigate();

  const readyText = useMemo(() => {
    if (!file) return "Choose a CSV file to begin";
    return `Ready: ${file.name}`;
  }, [file]);

  const onUpload = async () => {
    if (!file) return;
    setBusy(true);
    setMessage("");

    try {
      await pingHealth();
      await uploadDataset(file, "fast");
      setMessage("Upload successful. Fast mode started. Moving to Dashboard monitor...");
      setTimeout(() => navigate("/dashboard"), 500);
    } catch (err) {
      setMessage(err?.response?.data?.detail || "Upload failed. Ensure backend is running on :8000");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="grid gap-4 lg:grid-cols-[1.15fr_1fr]">
      <div className="glass-card p-5">
        <h2 className="font-display text-2xl font-semibold">Step 1: Upload Dataset</h2>
        <p className="mt-1 text-sm text-ink/65">
          This page only handles upload. Scheduling strategy changes are in Step 3.
        </p>

        <div className="mt-5 space-y-3">
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full rounded-xl border border-dashed border-ink/25 bg-white px-3 py-3"
            disabled={busy}
          />

          <button
            onClick={onUpload}
            disabled={busy || !file}
            className="w-full rounded-xl bg-gradient-to-r from-ember to-orange-400 px-4 py-2.5 font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Uploading..." : "Upload Dataset"}
          </button>
        </div>

        <p className="mt-3 text-sm text-ink/65">{readyText}</p>
        {message && <p className="mt-2 text-sm font-medium text-ink">{message}</p>}
      </div>

      <ProgressStatus status={status} />
    </section>
  );
}
