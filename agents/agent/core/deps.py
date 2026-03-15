"""Agent dependencies — injected via PydanticAI's RunContext.

Every tool receives RunContext[AgentDeps] as its first argument,
giving type-safe access to config, shared clients, and mock flags
without globals or singletons.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentDeps:
    mock_mode: bool = True
    mock_delay: float = 2.0
    mock_scenario: str = "premature_harvest"
    sandbox_dir: str = "./sandbox"
    robot_host: str = "localhost"
    robot_port: int = 50051
    camera_host: str = "localhost"
    camera_port: int = 8080
    robot_stream_url: str = ""
    state: dict[str, Any] = field(default_factory=dict)

    # ── Mock world clock & culture state ──────────────────────────────────

    _MOCK_STATE_KEYS = ("_protocol_day", "_culture_phase")

    def reset_mock_world(self) -> None:
        """Reset simulated world state for a fresh run."""
        robot_stream = self.state.get("_robot_stream")
        if robot_stream:
            robot_stream.reset()
        self.state.pop("_robot_stream", None)

        self.state["_protocol_day"] = 0
        self.state["_culture_phase"] = "growing"
        from agent.tools.analysis import reset_experiment_data
        reset_experiment_data()

    @property
    def protocol_day(self) -> int:
        return self.state.get("_protocol_day", 0)

    def advance_protocol_day(self) -> int:
        day = self.state.get("_protocol_day", 0) + 1
        self.state["_protocol_day"] = day
        return day

    @property
    def culture_phase(self) -> str:
        """Current cell culture phase: growing | dissociating | suspended | harvested."""
        return self.state.get("_culture_phase", "growing")

    def set_culture_phase(self, phase: str) -> None:
        self.state["_culture_phase"] = phase

    def sandbox_path(self) -> Path:
        p = Path(self.sandbox_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    async def mock_pause(self) -> None:
        if not (self.mock_mode and self.mock_delay > 0):
            return
        cancel: asyncio.Event | None = self.state.get("_cancel_event")
        remaining = self.mock_delay
        tick = 0.05
        while remaining > 0:
            if cancel and cancel.is_set():
                return
            await asyncio.sleep(min(tick, remaining))
            remaining -= tick
