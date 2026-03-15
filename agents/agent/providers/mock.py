"""Mock model — scenario-driven iPSC cell culture pipeline.

Loads the active scenario from agent/providers/scenarios/ and uses its
PIPELINE to simulate deterministic LLM tool-call sequences.

Config key: tools.mock_scenario  (default: "premature_harvest")
Available: premature_harvest | contamination | slow_growth
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, DeltaToolCalls, FunctionModel
from pydantic_ai.settings import ModelSettings

from agent.providers.scenarios import load_scenario
from agent.providers.scenarios.base import Scenario


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_user_query(messages: list[ModelMessage]) -> str:
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, UserPromptPart):
                    return part.content
    return "Set up and maintain iPSC-fast culture in T75"


def _get_tool_results(messages: list[ModelMessage]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    content = part.content
                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    results[part.tool_name] = content
    return results


def _count_tool_calls(messages: list[ModelMessage]) -> int:
    count = 0
    for msg in messages:
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    count += 1
    return count


# ── Model Implementation ────────────────────────────────────────────────────

def _build_response(messages: list[ModelMessage], scenario: Scenario) -> ModelResponse:
    query = _get_user_query(messages)
    results = _get_tool_results(messages)
    round_num = _count_tool_calls(messages)

    pipeline = scenario.pipeline
    if round_num < len(pipeline):
        step = pipeline[round_num]
        args = step["build_args"](query, results)
        return ModelResponse(parts=[
            TextPart(content=step["reasoning"]),
            ToolCallPart(
                tool_name=step["tool"],
                args=json.dumps(args),
                tool_call_id=f"mock_call_{round_num + 1}",
            ),
        ])

    completion = scenario.completion
    return ModelResponse(parts=[
        TextPart(content=completion.get("summary", "Experiment complete.")),
        ToolCallPart(
            tool_name="complete_experiment",
            args=json.dumps(completion),
            tool_call_id=f"mock_call_{round_num + 1}",
        ),
    ])


def create_mock_model(scenario_name: str = "premature_harvest") -> FunctionModel:
    """Create a FunctionModel that replays the named scenario's pipeline."""
    scenario = load_scenario(scenario_name)

    def mock_handler(
        messages: list[ModelMessage],
        info: AgentInfo,
        model_settings: ModelSettings | None = None,
    ) -> ModelResponse:
        return _build_response(messages, scenario)

    async def mock_stream_handler(
        messages: list[ModelMessage],
        info: AgentInfo,
        model_settings: ModelSettings | None = None,
    ) -> AsyncIterator[str | DeltaToolCalls]:
        response = _build_response(messages, scenario)

        for part in response.parts:
            if isinstance(part, TextPart):
                text = part.content
                chunk_size = 12
                for i in range(0, len(text), chunk_size):
                    yield text[i : i + chunk_size]
            elif isinstance(part, ToolCallPart):
                yield DeltaToolCalls({
                    0: DeltaToolCall(
                        name=part.tool_name,
                        json_args=part.args if isinstance(part.args, str) else json.dumps(part.args),
                        tool_call_id=part.tool_call_id,
                    )
                })

    return FunctionModel(mock_handler, stream_function=mock_stream_handler)
