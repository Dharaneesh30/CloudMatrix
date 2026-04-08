import { useEffect, useMemo, useState } from "react";

import { fetchStatus } from "../services/api";
import { PipelineContext } from "./pipelineContext";

export function PipelineProvider({ children }) {
  const [status, setStatus] = useState({
    status: "idle",
    progress: 0,
    rows_processed: 0,
    total_rows: 0,
    message: "Waiting for dataset upload",
    error: null,
  });
  const [refreshToken, setRefreshToken] = useState(0);
  const [dataVersion, setDataVersion] = useState(0);

  useEffect(() => {
    let active = true;

    const pull = async () => {
      try {
        const next = await fetchStatus();
        if (active) {
          setStatus(next);
          setRefreshToken(Date.now());
        }
      } catch {
        // keep previous status if backend is temporarily unreachable
      }
    };

    const kickoff = setTimeout(() => {
      void pull();
    }, 0);
    const timer = setInterval(pull, 2500);

    return () => {
      active = false;
      clearTimeout(kickoff);
      clearInterval(timer);
    };
  }, []);

  const computedHasRun = Number(status?.rows_processed || 0) > 0 || Number(status?.total_rows || 0) > 0;

  useEffect(() => {
    if (!computedHasRun) return;
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem("cm_has_run", "1");
    }
  }, [computedHasRun]);

  const value = useMemo(() => {
    const phase = String(status?.status || "idle");
    const isProcessing = phase === "queued" || phase === "processing";
    const isCompleted = phase === "completed";
    const stickyHasRun =
      typeof window !== "undefined" && window.sessionStorage.getItem("cm_has_run") === "1";
    const hasRun = computedHasRun || stickyHasRun;

    const notifyDataChanged = () => {
      setDataVersion((v) => v + 1);
    };

    return {
      status,
      setStatus,
      refreshToken,
      dataVersion,
      notifyDataChanged,
      isProcessing,
      isCompleted,
      hasRun,
    };
  }, [status, refreshToken, dataVersion, computedHasRun]);

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>;
}
