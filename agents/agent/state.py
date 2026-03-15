"""Runtime state — mutable server state, run history.

Separated from config (which is immutable after load).
"""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from typing import Any, Union

from pydantic_ai.models import Model

from agent.config import AppConfig
from agent.core.deps import AgentDeps
from agent.core.memory import RunMemory
from agent.providers import create_model

LOG = logging.getLogger(__name__)

MAX_RUN_HISTORY = 50


class AppState:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.provider: str = config.llm.active_provider
        self.model: Union[str, Model] = create_model(self.provider, config)
        self.deps: AgentDeps = AgentDeps(
            mock_mode=config.tools.mock_mode,
            mock_delay=config.tools.mock_delay,
            mock_scenario=config.tools.mock_scenario,
            sandbox_dir=config.agent.sandbox_dir,
            robot_host=config.tools.robot.host,
            robot_port=config.tools.robot.port,
            camera_host=config.tools.perception.camera_host,
            camera_port=config.tools.perception.camera_port,
            robot_stream_url=config.tools.robot_stream_url,
        )
        self.total_requests: int = 0
        self.total_tool_calls: int = 0
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.runs: OrderedDict[str, RunMemory] = OrderedDict()
        self.cancel_events: dict[str, asyncio.Event] = {}

    def new_run(self, query: str) -> RunMemory:
        run = RunMemory(query=query)
        self.runs[run.run_id] = run
        self.cancel_events[run.run_id] = asyncio.Event()
        if len(self.runs) > MAX_RUN_HISTORY:
            old_id, _ = self.runs.popitem(last=False)
            self.cancel_events.pop(old_id, None)
        self.deps.reset_mock_world()
        return run

    def snapshot(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.config.llm.get_provider(self.provider).model,
            "mock_mode": self.config.tools.mock_mode,
            "total_requests": self.total_requests,
            "total_tool_calls": self.total_tool_calls,
            "active_sessions": len(self.active_sessions),
            "total_runs": len(self.runs),
        }
