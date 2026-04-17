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
  const [backendReachable, setBackendReachable] = useState(true);

  useEffect(() => {
    let active = true;

    const pull = async () => {
      try {
        const next = await fetchStatus();
        if (active) {
          setStatus(next);
          setBackendReachable(true);
          setRefreshToken(Date.now());
        }
      } catch {
        if (active) {
          setBackendReachable(false);
        }
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
  const phase = String(status?.status || "idle");
  const isProcessingPhase = phase === "queued" || phase === "processing";

  useEffect(() => {
    if (typeof window !== "undefined") {
      if (computedHasRun) {
        window.sessionStorage.setItem("cm_has_run", "1");
      } else if (!isProcessingPhase && phase === "idle") {
        // Prevent stale cache from unlocking monitor/results without a real run.
        window.sessionStorage.removeItem("cm_has_run");
      }
    }
  }, [computedHasRun, isProcessingPhase, phase]);

  const value = useMemo(() => {
    const phaseNow = String(status?.status || "idle");
    const isProcessing = phaseNow === "queued" || phaseNow === "processing";
    const isCompleted = phaseNow === "completed";
    const stickyHasRun =
      typeof window !== "undefined" && window.sessionStorage.getItem("cm_has_run") === "1";
    const hasRun = computedHasRun || (stickyHasRun && phaseNow !== "idle");

    const notifyDataChanged = () => {
      setDataVersion((v) => v + 1);
    };

    return {
      status,
      setStatus,
      refreshToken,
      dataVersion,
      backendReachable,
      notifyDataChanged,
      isProcessing,
      isCompleted,
      hasRun,
    };
  }, [status, refreshToken, dataVersion, computedHasRun, backendReachable]);

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>;
}
