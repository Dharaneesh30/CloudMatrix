import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const checkBackend = async () => {
    try {
      await api.get("/health");
      return true;
    } catch {
      setMessage("Backend is not reachable. Start the server and try again.");
      return false;
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a CSV file first.");
      return;
    }

    const backendOk = await checkBackend();
    if (!backendOk) return;

    setLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post("/upload-dataset", formData);
      setMessage("Upload successful!");
      setTimeout(() => navigate("/task-sorting"), 1000);
    } catch (err) {
      console.error(err);
      setMessage(
        err.response?.data?.error ||
        err.response?.data?.message ||
        "Upload failed. Is backend running?"
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="page">
      <h2>Upload Cloud Task Dataset</h2>
      <p className="meta">Drop in your CSV file to start task sorting and allocation analysis.</p>

      <div className="panel-row">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          disabled={loading}
        />

        <button onClick={handleUpload} disabled={loading || !file}>
          {loading ? "Uploading..." : "Upload Dataset"}
        </button>
      </div>

      {message && (
        <p className={`status ${message.toLowerCase().includes("success") ? "success" : "error"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
