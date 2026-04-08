from __future__ import annotations

from datetime import datetime
from typing import Dict


class PipelineMonitor:
    def __init__(self) -> None:
        self.last_event: Dict | None = None

    def mark(self, status: str, detail: str) -> Dict:
        self.last_event = {
            "status": status,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return self.last_event


monitor = PipelineMonitor()
