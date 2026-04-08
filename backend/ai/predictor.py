from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from joblib import load
except Exception:  # pragma: no cover
    load = None

try:
    from .trainer import FEATURE_COLUMNS, train_execution_model
except ImportError:
    from trainer import FEATURE_COLUMNS, train_execution_model


def load_model(model_path: Path):
    if load is None or not model_path.exists():
        return None
    try:
        return load(model_path)
    except Exception:
        return None


def fallback_predict(chunk: pd.DataFrame) -> pd.Series:
    return (
        0.50 * chunk["execution_time"].astype(float)
        + 0.30 * chunk["cpu_request"].astype(float)
        + 0.20 * chunk["memory_request"].astype(float)
    )


def predict_execution_time(chunk: pd.DataFrame, model=None) -> pd.Series:
    if model is None:
        return fallback_predict(chunk)

    try:
        X = chunk[FEATURE_COLUMNS].astype(float)
        predictions = model.predict(X)
        return pd.Series(predictions, index=chunk.index)
    except Exception:
        return fallback_predict(chunk)


def get_or_train_model(
    training_df: pd.DataFrame,
    model_path: Path,
    algorithm: str = "linear",
):
    model = load_model(model_path)
    if model is not None:
        return model
    return train_execution_model(training_df, model_path=model_path, algorithm=algorithm)
