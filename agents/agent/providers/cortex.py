"""Cortex provider — calls Snowflake Cortex via the OpenAI-compatible REST API.

Uses the OpenAI SDK pointed at https://<host>/api/v2/cortex/v1 with PAT auth.
This supports tool calling, which the SQL CORTEX.COMPLETE() function does not.
"""

from __future__ import annotations

import configparser
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from openai import OpenAI
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    SystemPromptPart,
)
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, DeltaToolCalls, FunctionModel
from pydantic_ai.settings import ModelSettings

from agent.config import LLMProviderConfig

LOG = logging.getLogger(__name__)

_last_usage: dict[str, Any] = {}


def get_last_usage() -> dict[str, Any]:
    """Return the usage stats from the most recent Cortex API call."""
    return dict(_last_usage)


def _load_connection(name: str) -> dict[str, str]:
    """Load host and token from ~/.snowflake/connections.toml."""
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.snowflake/connections.toml"))
    if name not in config:
        raise ValueError(
            f"Connection '{name}' not found in ~/.snowflake/connections.toml. "
            f"Available: {list(config.sections())}"
        )
    sec = config[name]
    return {
        "host": sec.get("host", "").strip('"'),
        "token": sec.get("token", "").strip('"'),
        "account": sec.get("account", "").strip('"'),
    }


def _convert_messages(messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """Convert PydanticAI messages to OpenAI-style message dicts for Cortex."""
    out: list[dict[str, Any]] = []

    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    out.append({"role": "system", "content": part.content})
                elif isinstance(part, UserPromptPart):
                    out.append({"role": "user", "content": part.content})
                elif isinstance(part, ToolReturnPart):
                    out.append({
                        "role": "tool",
                        "tool_call_id": part.tool_call_id or "",
                        "content": json.dumps(part.content) if not isinstance(part.content, str) else part.content,
                    })
                elif isinstance(part, RetryPromptPart):
                    retry_content = part.content if isinstance(part.content, str) else json.dumps(part.content)
                    if part.tool_call_id and part.tool_name:
                        # Only use tool role if the preceding assistant message
                        # actually has a matching tool_call (i.e., a real tool retry,
                        # not a synthetic output-tool retry from PydanticAI).
                        prev_assistant = next(
                            (m for m in reversed(out)
                             if m.get("role") == "assistant" and m.get("tool_calls")),
                            None,
                        )
                        has_match = prev_assistant and any(
                            tc.get("id") == part.tool_call_id
                            for tc in prev_assistant.get("tool_calls", [])
                        )
                        if has_match:
                            out.append({
                                "role": "tool",
                                "tool_call_id": part.tool_call_id,
                                "content": retry_content,
                            })
                        else:
                            out.append({"role": "user", "content": retry_content})
                    else:
                        out.append({"role": "user", "content": retry_content})
        elif isinstance(msg, ModelResponse):
            text_content = ""
            tool_calls: list[dict[str, Any]] = []

            for part in msg.parts:
                if isinstance(part, TextPart):
                    text_content = text_content + part.content if text_content else part.content
                elif isinstance(part, ToolCallPart):
                    args_str = part.args if isinstance(part.args, str) else json.dumps(part.args)
                    if not args_str or args_str == "null":
                        args_str = "{}"
                    tool_calls.append({
                        "id": part.tool_call_id or "",
                        "type": "function",
                        "function": {
                            "name": part.tool_name,
                            "arguments": args_str,
                        },
                    })

            entry: dict[str, Any] = {"role": "assistant"}
            if tool_calls:
                entry["content"] = text_content or None
                entry["tool_calls"] = tool_calls
            else:
                entry["content"] = text_content or ""
            out.append(entry)

    return out


def _build_tools_schema(info: AgentInfo) -> list[dict[str, Any]]:
    """Convert PydanticAI tool definitions to OpenAI-style tool schema for Cortex."""
    tools: list[dict[str, Any]] = []
    for td in info.function_tools:
        tools.append({
            "type": "function",
            "function": {
                "name": td.name,
                "description": td.description,
                "parameters": td.parameters_json_schema,
            },
        })
    for td in info.output_tools:
        tools.append({
            "type": "function",
            "function": {
                "name": td.name,
                "description": td.description,
                "parameters": td.parameters_json_schema,
            },
        })
    return tools


def _parse_cortex_response(response: Any) -> ModelResponse:
    """Parse a Cortex REST API response (OpenAI ChatCompletion) into PydanticAI ModelResponse.

    Enforces single tool call per turn: if the model returns multiple parallel
    tool calls, only the first is kept. This forces step-by-step reasoning.
    """
    if hasattr(response, "choices"):
        message = response.choices[0].message
        parts: list[Any] = []

        if message.content and message.content.strip():
            parts.append(TextPart(content=message.content))

        if message.tool_calls:
            tc = message.tool_calls[0]
            if len(message.tool_calls) > 1:
                LOG.info(
                    "Cortex returned %d parallel tool calls, keeping only first: %s",
                    len(message.tool_calls), tc.function.name,
                )
            raw_args = tc.function.arguments
            if not raw_args or raw_args == "null":
                raw_args = "{}"
            parts.append(ToolCallPart(
                tool_name=tc.function.name,
                args=raw_args,
                tool_call_id=tc.id or "",
            ))

        if not parts:
            parts.append(TextPart(content=""))

        return ModelResponse(parts=parts)

    # Fallback: raw dict/string (shouldn't happen with REST API, but defensive)
    if isinstance(response, str):
        response = json.loads(response)
    if not isinstance(response, dict):
        return ModelResponse(parts=[TextPart(content=str(response))])

    choices = response.get("choices", [])
    if not choices:
        content = response.get("message", response.get("content", ""))
        if isinstance(content, dict):
            content = content.get("content", json.dumps(content))
        return ModelResponse(parts=[TextPart(content=str(content))])

    choice = choices[0]
    message_dict = choice.get("message") or choice.get("messages", {})
    if isinstance(message_dict, str):
        return ModelResponse(parts=[TextPart(content=message_dict)])

    parts = []
    content = message_dict.get("content")
    if content:
        parts.append(TextPart(content=str(content)))

    for tc in message_dict.get("tool_calls", []):
        fn = tc.get("function", {})
        raw_args = fn.get("arguments", "{}")
        if not raw_args or raw_args == "null":
            raw_args = "{}"
        parts.append(ToolCallPart(
            tool_name=fn.get("name", ""),
            args=raw_args,
            tool_call_id=tc.get("id", ""),
        ))

    if not parts:
        parts.append(TextPart(content=""))

    return ModelResponse(parts=parts)


def _call_cortex(
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
    temperature: float,
    max_tokens: int,
) -> Any:
    """Call Cortex via the OpenAI-compatible REST API."""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["parallel_tool_calls"] = False

    return client.chat.completions.create(**kwargs)


def create_cortex_model(provider_cfg: LLMProviderConfig) -> FunctionModel:
    """Create a PydanticAI FunctionModel backed by the Cortex REST API."""

    if provider_cfg.snowflake_connection_name:
        conn_info = _load_connection(provider_cfg.snowflake_connection_name)
        host = conn_info["host"]
        token = conn_info["token"]
    else:
        # Manual config: host derived from account, token from env
        account = provider_cfg.snowflake_account
        host = f"{account}.snowflakecomputing.com"
        token = os.environ.get("SNOWFLAKE_PAT", "")
        if not token:
            raise ValueError(
                "Cortex REST API requires a PAT. Set SNOWFLAKE_PAT env var "
                "or use snowflake_connection_name in config."
            )

    base_url = f"https://{host}/api/v2/cortex/v1"
    client = OpenAI(api_key=token, base_url=base_url)
    LOG.info("Cortex: using REST API at %s", base_url)

    model_name = provider_cfg.model

    def handler(
        messages: list[ModelMessage],
        info: AgentInfo,
        model_settings: ModelSettings | None = None,
    ) -> ModelResponse:
        cortex_msgs = _convert_messages(messages)
        tools = _build_tools_schema(info) or None

        temp = float((model_settings or {}).get("temperature", 0))
        max_tok = int((model_settings or {}).get("max_tokens", 4096))

        LOG.info("Cortex request: %d messages, %d tools", len(cortex_msgs), len(tools or []))
        for i, m in enumerate(cortex_msgs):
            role = m.get("role", "?")
            tc = m.get("tool_calls")
            tcid = m.get("tool_call_id")
            content_preview = str(m.get("content", ""))[:80]
            if tc:
                tc_names = [t["function"]["name"] for t in tc]
                LOG.info("  msg[%d] role=%s tool_calls=%s content=%s", i, role, tc_names, content_preview)
            elif tcid:
                LOG.info("  msg[%d] role=%s tool_call_id=%s content=%s", i, role, tcid, content_preview)
            else:
                LOG.info("  msg[%d] role=%s content=%s...", i, role, content_preview)
        context_chars = sum(len(json.dumps(m)) for m in cortex_msgs)

        raw = _call_cortex(client, model_name, cortex_msgs, tools, temp, max_tok)
        response = _parse_cortex_response(raw)

        usage = getattr(raw, "usage", None)
        usage_info = {}
        if usage:
            usage_info = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        response._cortex_usage = usage_info  # type: ignore[attr-defined]
        response._cortex_context_chars = context_chars  # type: ignore[attr-defined]
        response._cortex_message_count = len(cortex_msgs)  # type: ignore[attr-defined]

        _last_usage.update({
            "usage": usage_info,
            "context_chars": context_chars,
            "message_count": len(cortex_msgs),
        })

        part_summary = ", ".join(
            f"ToolCall({p.tool_name})" if isinstance(p, ToolCallPart)
            else f"Text({len(p.content)}ch)" if isinstance(p, TextPart)
            else type(p).__name__
            for p in response.parts
        )
        tokens_str = f" tokens={usage_info}" if usage_info else ""
        LOG.info(
            "Cortex response parts: [%s] msgs=%d ctx_chars=%d%s",
            part_summary, len(cortex_msgs), context_chars, tokens_str,
        )
        return response

    async def stream_handler(
        messages: list[ModelMessage],
        info: AgentInfo,
        model_settings: ModelSettings | None = None,
    ) -> AsyncIterator[str | DeltaToolCalls]:
        response = handler(messages, info, model_settings)

        tool_idx = 0
        for part in response.parts:
            if isinstance(part, TextPart) and part.content:
                chunk_size = 20
                text = part.content
                for i in range(0, len(text), chunk_size):
                    yield text[i : i + chunk_size]
            elif isinstance(part, ToolCallPart):
                yield DeltaToolCalls({
                    tool_idx: DeltaToolCall(
                        name=part.tool_name,
                        json_args=part.args if isinstance(part.args, str) else json.dumps(part.args),
                        tool_call_id=part.tool_call_id,
                    )
                })
                tool_idx += 1

    return FunctionModel(handler, stream_function=stream_handler)
