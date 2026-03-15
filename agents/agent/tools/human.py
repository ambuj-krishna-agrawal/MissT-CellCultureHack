"""Human-in-the-loop tool — pauses the agent and requests operator input.

Supports structured input fields that the UI renders dynamically:
  - text:         free-form text input (with optional placeholder/default)
  - number:       numeric input (with optional min/max/step/unit)
  - select:       single-select from options
  - multi_select: multi-select from options
  - confirm:      yes/no toggle
  - info:         read-only display block (no user input, just information)

The LLM decides which fields to present based on what it needs from the user.
The UI renders each field type with appropriate controls.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def request_human_input(
    ctx: RunContext[AgentDeps],
    message: str,
    input_fields: list[dict[str, Any]] | None = None,
    info_blocks: list[dict[str, str]] | None = None,
    upcoming_actions: list[dict[str, str]] | None = None,
) -> dict:
    """Pause execution and request input from the human operator.

    Use this when a decision requires human judgment — e.g. protocol approval,
    parameter selection, or safety-critical confirmations.

    Args:
        message: Markdown-formatted message to display to the operator.
            Explain context, present calculations, or summarize the situation.
        input_fields: List of input fields the operator should fill in. Each field is a dict:
            - id (str): unique field identifier, used as key in the response
            - type (str): one of "text", "number", "select", "multi_select", "confirm", "info"
            - label (str): display label for the field
            - required (bool, optional): whether the field must be filled (default True)

            Type-specific keys:
            - text: placeholder (str), default (str)
            - number: min (float), max (float), step (float), unit (str), default (float)
            - select: options (list of {value: str, label: str}), default (str)
            - multi_select: options (list of {value: str, label: str}), defaults (list of str)
            - confirm: default (bool), confirm_label (str), deny_label (str)
            - info: content (str) — read-only markdown content, no user input collected

            Example input_fields:
            [
                {"id": "density", "type": "select", "label": "Seeding density",
                 "options": [
                     {"value": "12", "label": "12k cells/cm² (default, 4 days)"},
                     {"value": "15", "label": "15k cells/cm² (3 days)"},
                     {"value": "20", "label": "20k cells/cm² (2 days)"}
                 ], "default": "12"},
                {"id": "target_cells", "type": "number", "label": "Target cell count",
                 "min": 1000000, "max": 1000000000, "unit": "cells", "default": 15000000},
                {"id": "reseed", "type": "confirm", "label": "Re-seed after harvest?",
                 "default": true, "confirm_label": "Yes", "deny_label": "No"},
                {"id": "notes", "type": "text", "label": "Special instructions",
                 "placeholder": "Any modifications or notes...", "required": false}
            ]

        info_blocks: Optional list of info panels to display. Each dict has:
            - title (str): block title
            - content (str): markdown content
            - style (str, optional): "default", "warning", "success", "info"

        upcoming_actions: Optional list of next actions if approved. Each dict has:
            action (str), scope (str), tool (str, optional).
    """
    await ctx.deps.mock_pause()

    callback = ctx.deps.state.get("_human_input_callback")
    if callback is None:
        return _auto_response(input_fields)

    future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
    ctx.deps.state["_human_input_future"] = future

    await callback(message, input_fields, info_blocks, upcoming_actions)

    cancel_event: asyncio.Event | None = ctx.deps.state.get("_cancel_event")

    if cancel_event:
        cancel_task = asyncio.create_task(_wait_cancel(cancel_event))
        done, pending = await asyncio.wait(
            [asyncio.ensure_future(future), cancel_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()

        if future.done():
            response = future.result()
        else:
            ctx.deps.state.pop("_human_input_future", None)
            return {
                "response": "Cancelled by user",
                "respondent": "system",
                "auto": True,
            }
    else:
        response = await future

    ctx.deps.state.pop("_human_input_future", None)

    parsed_response: dict[str, Any] = {"raw": response}
    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict):
            parsed_response = parsed
    except (json.JSONDecodeError, TypeError):
        parsed_response = {"raw": response}

    return {
        "response": parsed_response.get("action", response),
        "respondent": "human_operator",
        "auto": False,
        "fields": parsed_response.get("fields", {}),
        "comments": parsed_response.get("comments"),
    }


def _auto_response(input_fields: list[dict[str, Any]] | None) -> dict:
    """Generate automatic response using defaults when no operator is connected."""
    fields: dict[str, Any] = {}
    if input_fields:
        for field in input_fields:
            fid = field.get("id", "")
            ftype = field.get("type", "text")
            if ftype == "info":
                continue
            if "default" in field:
                fields[fid] = field["default"]
            elif "defaults" in field:
                fields[fid] = field["defaults"]
            elif ftype == "confirm":
                fields[fid] = True
            elif ftype == "select" and field.get("options"):
                fields[fid] = field["options"][0].get("value", "")
            elif ftype == "number":
                fields[fid] = field.get("min", 0)
            else:
                fields[fid] = ""
    return {
        "response": "Auto-approved (no operator connected)",
        "respondent": "system",
        "auto": True,
        "fields": fields,
    }


async def _wait_cancel(event: asyncio.Event) -> None:
    await event.wait()
