from threading import Lock


class PipelineStatus:
    """Thread-safe status tracker for background processing."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._state = {
            "status": "idle",
            "progress": 0,
            "rows_processed": 0,
            "total_rows": 0,
            "message": "Waiting for dataset upload",
            "error": None,
        }

    def reset(self) -> None:
        with self._lock:
            self._state.update(
                {
                    "status": "processing",
                    "progress": 0,
                    "rows_processed": 0,
                    "total_rows": 0,
                    "message": "Pipeline started",
                    "error": None,
                }
            )

    def update(self, **kwargs) -> None:
        with self._lock:
            self._state.update(kwargs)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._state)


pipeline_status = PipelineStatus()
