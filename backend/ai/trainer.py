from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from joblib import dump
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
except Exception:  # pragma: no cover
    dump = None
    RandomForestRegressor = None
    LinearRegression = None


FEATURE_COLUMNS = ["priority", "cpu_request", "memory_request"]
TARGET_COLUMN = "execution_time"


def train_execution_model(
    training_df: pd.DataFrame,
    model_path: Path,
    algorithm: str = "linear",
):
    """
    Train and persist execution-time predictor model.
    Returns sklearn model or None when sklearn isn't installed.
    """
    if LinearRegression is None:
        return None

    data = training_df.copy()
    data = data.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
    if data.empty:
        return None

    X = data[FEATURE_COLUMNS].astype(float)
    y = data[TARGET_COLUMN].astype(float)

    if algorithm == "random_forest" and RandomForestRegressor is not None:
        model = RandomForestRegressor(
            n_estimators=80,
            random_state=42,
            n_jobs=-1,
            max_depth=12,
        )
    else:
        model = LinearRegression()

    model.fit(X, y)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if dump is not None:
        dump(model, model_path)
    return model
