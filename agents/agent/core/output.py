"""Structured output type for agent completion.

The agent MUST call this output tool to signal it has finished.
Plain text responses will NOT end the run — only an explicit
call to the `complete_experiment` tool triggers completion.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExperimentComplete(BaseModel):
    """Call this tool when the current task or experiment phase is complete."""

    summary: str = Field(description="Concise summary of what was accomplished in this run")
    status: str = Field(
        description="Completion status: 'completed', 'needs_review', 'paused', or 'error'",
        default="completed",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Recommended next steps or follow-up actions for the scientist",
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Key observations, measurements, or decisions made during this run",
    )
