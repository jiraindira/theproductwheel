import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class RunLogger:
    """
    Append-only JSONL run logger.

    Each call writes one JSON object per line to log_path.
    This is safe for streaming and avoids corrupting a single large JSON file.
    """
    run_id: str
    post_slug: str
    log_path: Path

    def _write(self, payload: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def start(self, agent: str, input: Any) -> None:
        self._write({
            "ts": utc_iso(),
            "run_id": self.run_id,
            "post_slug": self.post_slug,
            "agent": agent,
            "event": "start",
            "status": "ok",
            "input": input,
        })

    def end(self, agent: str, output: Any, metrics: Optional[dict[str, Any]] = None) -> None:
        self._write({
            "ts": utc_iso(),
            "run_id": self.run_id,
            "post_slug": self.post_slug,
            "agent": agent,
            "event": "end",
            "status": "ok",
            "output": output,
            "metrics": metrics or {},
        })

    def error(self, agent: str, input: Any, err: Exception) -> None:
        self._write({
            "ts": utc_iso(),
            "run_id": self.run_id,
            "post_slug": self.post_slug,
            "agent": agent,
            "event": "error",
            "status": "error",
            "input": input,
            "error": {
                "type": err.__class__.__name__,
                "message": str(err),
            }
        })
