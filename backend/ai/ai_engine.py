from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from .predictor import get_or_train_model, predict_execution_time
except ImportError:
    from predictor import get_or_train_model, predict_execution_time


class AIEngine:
    """Facade to train/load model and run execution-time predictions."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.model = None

    def warmup(self, sample_df: pd.DataFrame) -> None:
        self.model = get_or_train_model(sample_df, model_path=self.model_path)

    def predict(self, chunk_df: pd.DataFrame) -> pd.Series:
        return predict_execution_time(chunk_df, model=self.model)
