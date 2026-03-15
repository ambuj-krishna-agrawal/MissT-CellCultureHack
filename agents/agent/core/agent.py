"""PydanticAI agent definition.

To add a new tool:
  1. Write an async function in agent/tools/ with RunContext[AgentDeps] first param
  2. Add it to ALL_TOOLS in agent/tools/__init__.py
  3. Done. PydanticAI generates the JSON schema from type hints + docstring.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent, ToolOutput

from agent.core.deps import AgentDeps
from agent.core.output import ExperimentComplete
from agent.tools import ALL_TOOLS

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system.md"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "You are a cell culture automation assistant."


cell_culture_agent: Agent[AgentDeps, ExperimentComplete] = Agent(
    "test",
    deps_type=AgentDeps,
    output_type=ToolOutput(
        ExperimentComplete,
        name="complete_experiment",
        description=(
            "Call this tool when a task or experiment phase is fully complete. "
            "Provide a summary, status, key findings, and next steps. "
            "For simple greetings or questions, still call this with a brief summary."
        ),
    ),
    tools=ALL_TOOLS,
    system_prompt=_load_prompt(),
)
