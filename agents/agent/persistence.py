"""Session persistence — multi-run sessions as JSON files.

Storage: sessions/ directory at project root.
Each session: sessions/{session_id}.json
A session groups multiple runs (queries) in the same thread.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)

SESSIONS_DIR = Path("sessions")


def _ensure_dir() -> None:
    SESSIONS_DIR.mkdir(exist_ok=True)


def _migrate_old_format(data: dict[str, Any]) -> dict[str, Any]:
    """Convert old single-run format to multi-run session format."""
    return {
        "session_id": data.get("run_id", "unknown"),
        "name": (data.get("query", "") or "")[:60] or "Untitled",
        "runs": [data],
        "provider": data.get("provider", ""),
        "model": data.get("model", ""),
        "mock_mode": data.get("mock_mode", False),
        "created_at": data.get("started_at", time.time()),
        "updated_at": data.get("completed_at") or data.get("started_at", time.time()),
    }


def create_session(session_id: str, name: str = "New session") -> dict[str, Any]:
    data: dict[str, Any] = {
        "session_id": session_id,
        "name": name,
        "runs": [],
        "provider": "",
        "model": "",
        "mock_mode": False,
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    save_session(data)
    return data


def save_session(data: dict[str, Any]) -> None:
    _ensure_dir()
    session_id = data.get("session_id", "unknown")
    path = SESSIONS_DIR / f"{session_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    LOG.debug("Session saved: %s", path)


def load_session(session_id: str) -> dict[str, Any] | None:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    if "session_id" not in data:
        data = _migrate_old_format(data)
        save_session(data)
    return data


def list_sessions() -> list[dict[str, Any]]:
    _ensure_dir()
    sessions: list[dict[str, Any]] = []
    for path in sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(path) as f:
                data = json.load(f)
            if "session_id" not in data:
                data = _migrate_old_format(data)
                save_session(data)
            runs = data.get("runs", [])
            latest_run = runs[-1] if runs else None
            total_steps = sum(len(r.get("steps", [])) for r in runs)
            sessions.append({
                "session_id": data["session_id"],
                "name": data.get("name", "Untitled"),
                "status": latest_run["status"] if latest_run else "empty",
                "run_count": len(runs),
                "total_steps": total_steps,
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
            })
        except Exception:
            continue
    return sessions


def delete_session(session_id: str) -> bool:
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
