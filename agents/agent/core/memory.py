"""Structured run memory — tracks every step the agent takes.

Each Step is a self-contained record (tool name, input, output, timing, reasoning).
Designed for persistence and future compression.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Step:
    id: str
    step_number: int
    tool_name: str
    arguments: dict[str, Any]
    reasoning: str | None = None
    thinking: str | None = None
    result: Any | None = None
    status: str = "running"
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    context_messages: int = 0
    context_chars: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cumulative_context_chars: int = 0

    @property
    def duration_ms(self) -> float | None:
        if self.completed_at is not None:
            return round((self.completed_at - self.started_at) * 1000, 1)
        return None

    def complete(self, result: Any) -> None:
        self.result = result
        self.status = "completed"
        self.completed_at = time.time()

    def fail(self, error: str) -> None:
        self.error = error
        self.status = "error"
        self.completed_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "step_number": self.step_number,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "reasoning": self.reasoning,
            "thinking": self.thinking,
            "result": self.result,
            "status": self.status,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_messages": self.context_messages,
            "context_chars": self.context_chars,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cumulative_context_chars": self.cumulative_context_chars,
        }

    def summary(self) -> str:
        status = "OK" if self.status == "completed" else self.status.upper()
        dur = f" ({self.duration_ms:.0f}ms)" if self.duration_ms else ""
        return f"Step {self.step_number}: {self.tool_name} [{status}]{dur}"


@dataclass
class RunMemory:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    query: str = ""
    status: str = "running"
    steps: list[Step] = field(default_factory=list)
    thinking_chunks: list[str] = field(default_factory=list)
    content_chunks: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    final_output: str | None = None

    def add_step(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        reasoning: str | None = None,
        thinking: str | None = None,
    ) -> Step:
        step = Step(
            id=uuid.uuid4().hex[:8],
            step_number=len(self.steps) + 1,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
            thinking=thinking,
        )
        self.steps.append(step)
        return step

    def complete_step(self, step_id: str, result: Any) -> None:
        for step in self.steps:
            if step.id == step_id:
                step.complete(result)
                return

    def fail_step(self, step_id: str, error: str) -> None:
        for step in self.steps:
            if step.id == step_id:
                step.fail(error)
                return

    def finish(self, output: str) -> None:
        self.final_output = output
        self.status = "completed"
        self.completed_at = time.time()

    def stop(self) -> None:
        self.status = "stopped"
        self.completed_at = time.time()
        for step in self.steps:
            if step.status == "running":
                step.fail("Run stopped by user")

    @property
    def duration_ms(self) -> float | None:
        if self.completed_at is not None:
            return round((self.completed_at - self.started_at) * 1000, 1)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "query": self.query,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "step_count": len(self.steps),
            "final_output": self.final_output,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    def compress(self) -> str:
        lines = [f"Run: {self.query}"]
        for step in self.steps:
            lines.append(f"  {step.summary()}")
        if self.final_output:
            lines.append(f"  Output: {self.final_output[:200]}")
        return "\n".join(lines)
