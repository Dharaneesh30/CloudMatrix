import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { fetchStatus } from "../services/api";

const PipelineContext = createContext(null);

export function PipelineProvider({ children }) {
  const [status, setStatus] = useState({
    status: "idle",
    progress: 0,
    rows_processed: 0,
    total_rows: 0,
    message: "Waiting for dataset upload",
    error: null,
  });

  useEffect(() => {
    let active = true;

    const pull = async () => {
      try {
        const next = await fetchStatus();
        if (active) setStatus(next);
      } catch {
        // keep previous status if backend is temporarily unreachable
      }
    };

    pull();
    const timer = setInterval(pull, 2500);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const value = useMemo(() => {
    const phase = String(status?.status || "idle");
    const isProcessing = phase === "queued" || phase === "processing";
    const isCompleted = phase === "completed";
    const hasRun = Number(status?.rows_processed || 0) > 0 || Number(status?.total_rows || 0) > 0;

    return {
      status,
      setStatus,
      isProcessing,
      isCompleted,
      hasRun,
    };
  }, [status]);

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>;
}

export function usePipeline() {
  const ctx = useContext(PipelineContext);
  if (!ctx) {
    throw new Error("usePipeline must be used within PipelineProvider");
  }
  return ctx;
}
