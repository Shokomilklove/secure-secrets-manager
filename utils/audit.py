import json
import os
from datetime import datetime, timezone


def log_event(data_dir: str, event: str, user_id: str | None, detail: dict | None = None) -> None:
    os.makedirs(data_dir, exist_ok=True)
    log_path = os.path.join(data_dir, "audit.log")
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id,
        "detail": detail or {},
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
