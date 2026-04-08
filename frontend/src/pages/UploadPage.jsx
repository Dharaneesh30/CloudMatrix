import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import ProgressStatus from "../components/ProgressStatus";
import { usePipeline } from "../context/usePipeline";
import { pingHealth, uploadDataset } from "../services/api";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [unusedServers, setUnusedServers] = useState(3);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const { status, notifyDataChanged } = usePipeline();
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
      await uploadDataset(file, unusedServers);
      notifyDataChanged();
      setMessage("Upload successful. Automatic pipeline started. Moving to dashboard...");
      setTimeout(() => navigate("/dashboard"), 500);
    } catch (err) {
      setMessage(err?.response?.data?.detail || "Upload failed. Ensure backend is running on :8000");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="grid gap-4 lg:grid-cols-[1.15fr_1fr]">
      <div className="glass-card p-5 md:p-6">
        <h2 className="font-display text-2xl font-semibold">Step 1: Upload Dataset</h2>
        <p className="mt-1 text-sm text-ink/65">
          Upload a CSV and CloudMatrix AI will automatically run the full scheduling pipeline.
        </p>

        <div className="mt-5 space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-ink/70">Unused Servers (start capacity)</label>
            <input
              type="number"
              min={1}
              max={500}
              value={unusedServers}
              onChange={(e) => setUnusedServers(Math.max(1, Number(e.target.value || 1)))}
              className="input-modern"
              disabled={busy}
            />
          </div>

          <label className="file-drop block cursor-pointer">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
              disabled={busy}
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink">Choose Dataset (CSV)</p>
                <p className="mt-0.5 text-xs text-ink/65">
                  {file ? file.name : "No file selected yet"}
                </p>
              </div>
              <span className="btn-secondary px-3 py-1.5 text-xs">Browse</span>
            </div>
          </label>

          <button
            onClick={onUpload}
            disabled={busy || !file}
            className="btn-primary w-full"
          >
            {busy ? "Uploading..." : "Upload Dataset"}
          </button>
        </div>

        <p className="mt-3 text-sm text-ink/65">{readyText}</p>
        {file && <span className="chip mt-2">CSV Ready</span>}
        {message && <p className="mt-2 text-sm font-medium text-ink">{message}</p>}
      </div>

      <ProgressStatus status={status} />
    </section>
  );
}
