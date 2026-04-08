from __future__ import annotations

import pandas as pd


def predict_server_load(chunk: pd.DataFrame) -> pd.Series:
    """
    Lightweight load proxy to support metrics and future load models.
    """
    cpu = chunk["cpu_request"].astype(float)
    memory = chunk["memory_request"].astype(float)
    exec_t = chunk["predicted_execution_time"].astype(float).clip(lower=0.1)
    return (0.55 * cpu) + (0.35 * memory) + (0.10 * exec_t)
