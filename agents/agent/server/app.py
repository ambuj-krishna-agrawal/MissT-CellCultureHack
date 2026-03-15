"""FastAPI server with multi-run sessions, stop/resume, and human-in-the-loop.

Endpoints:
  GET  /api/health          — health + runtime stats
  GET  /api/tools           — registered tool list
  GET  /api/config          — current config
  GET  /api/sessions        — persisted session list
  GET  /api/sessions/{id}   — load persisted session
  POST /api/sessions        — create empty session
  WS   /ws                  — streaming agent events
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai import (
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
)
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from dotenv import load_dotenv
load_dotenv()

from agent.core.agent import cell_culture_agent
from agent.core.memory import RunMemory, Step
from agent.config import load_config
from agent.persistence import (
    save_session,
    load_session,
    list_sessions,
    create_session as create_session_file,
)
from agent.state import AppState
from agent.providers.cortex import get_last_usage

LOG = logging.getLogger(__name__)

_state: AppState | None = None


def _get_state() -> AppState:
    assert _state is not None, "Server not initialized"
    return _state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _state
    config = load_config()

    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    _state = AppState(config)
    LOG.info(
        "Agent ready: provider=%s, model=%s, mock=%s",
        _state.provider,
        config.llm.get_provider(_state.provider).model,
        config.tools.mock_mode,
    )
    yield
    LOG.info("Server shutdown")


app = FastAPI(title="CellCultureAgent", version="0.8.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_args(args: Any) -> dict:
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {"raw": args}
    return {"raw": str(args)}


def _serialize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, default=str)


def _evt(event_type: str, data: dict) -> dict:
    return {
        "event_type": event_type,
        "data": data,
        "timestamp": time.time(),
        "event_id": uuid.uuid4().hex[:8],
    }


async def _safe_send(ws: WebSocket, payload: dict) -> bool:
    """Send JSON on a WebSocket, returning False if the connection is already closed."""
    try:
        await ws.send_json(payload)
        return True
    except (RuntimeError, WebSocketDisconnect):
        return False


def _build_model_settings(state: AppState) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "temperature": state.config.llm.temperature,
        "max_tokens": state.config.llm.max_tokens,
    }
    if state.provider == "anthropic":
        budget = state.config.llm.thinking_budget
        settings["anthropic_thinking"] = {"type": "enabled", "budget_tokens": budget}
    return settings


def _persist_session(state: AppState, session_data: dict[str, Any], run: RunMemory) -> None:
    try:
        run_dict = run.to_dict()
        runs = session_data.get("runs", [])
        idx = next((i for i, r in enumerate(runs) if r.get("run_id") == run.run_id), None)
        if idx is not None:
            runs[idx] = run_dict
        else:
            runs.append(run_dict)
        session_data["runs"] = runs
        session_data["updated_at"] = time.time()
        session_data["provider"] = state.provider
        session_data["model"] = state.config.llm.get_provider(state.provider).model
        session_data["mock_mode"] = state.config.tools.mock_mode
        save_session(session_data)
    except Exception as e:
        LOG.warning("Failed to persist session: %s", e)


def _reconstruct_message_history(query: str, completed_steps: list[dict]) -> list[ModelMessage]:
    """Rebuild PydanticAI message history from completed steps for resume."""
    history: list[ModelMessage] = [
        ModelRequest(parts=[UserPromptPart(content=query)]),
    ]
    for step in completed_steps:
        resp_parts: list[Any] = []
        if step.get("reasoning"):
            resp_parts.append(TextPart(content=step["reasoning"]))
        args_raw = step.get("arguments", {})
        resp_parts.append(ToolCallPart(
            tool_name=step["tool_name"],
            args=json.dumps(args_raw) if isinstance(args_raw, dict) else str(args_raw),
            tool_call_id=f"resume_{step['step_number']}",
        ))
        history.append(ModelResponse(parts=resp_parts))

        result_content = step.get("result")
        if isinstance(result_content, str):
            try:
                result_content = json.loads(result_content)
            except (json.JSONDecodeError, TypeError):
                pass
        history.append(ModelRequest(parts=[
            ToolReturnPart(
                tool_name=step["tool_name"],
                content=result_content,
                tool_call_id=f"resume_{step['step_number']}",
            ),
        ]))
    return history


def _rebuild_run_from_stopped(stopped_run: dict[str, Any]) -> RunMemory:
    """Create a RunMemory pre-populated with the completed steps from a stopped run."""
    run = RunMemory(
        run_id=stopped_run["run_id"],
        query=stopped_run["query"],
        started_at=stopped_run.get("started_at", time.time()),
    )
    for step_data in stopped_run.get("steps", []):
        if step_data["status"] != "completed":
            continue
        step = Step(
            id=step_data["id"],
            step_number=step_data["step_number"],
            tool_name=step_data["tool_name"],
            arguments=step_data.get("arguments", {}),
            reasoning=step_data.get("reasoning"),
            thinking=step_data.get("thinking"),
            result=step_data.get("result"),
            status="completed",
            started_at=step_data.get("started_at", time.time()),
            completed_at=step_data.get("completed_at"),
        )
        run.steps.append(step)
    return run


def _rebuild_mock_world_from_steps(state: AppState, completed_steps: list[dict]) -> None:
    """Restore mock world state from completed steps so resumed tools behave correctly."""
    state.deps.reset_mock_world()
    for step in completed_steps:
        result = step.get("result")
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(result, dict):
            continue
        if "protocol_day" in result:
            state.deps.state["_protocol_day"] = result["protocol_day"]
        if "culture_phase" in result:
            state.deps.state["_culture_phase"] = result["culture_phase"]


async def _stream_to_ws(
    ws: WebSocket,
    query: str,
    session_id: str,
    cancel_event: asyncio.Event,
    *,
    message_history: list[ModelMessage] | None = None,
    existing_run: RunMemory | None = None,
    is_resume: bool = False,
) -> None:
    state = _get_state()
    state.total_requests += 1

    session_data = load_session(session_id)
    if session_data is None:
        session_data = create_session_file(session_id, query[:60] or "New session")

    if session_data.get("name") == "New session" and query.strip():
        session_data["name"] = query[:60]

    if existing_run is not None:
        run = existing_run
        run.status = "running"
        state.runs[run.run_id] = run
    else:
        run = state.new_run(query)

    call_id_to_step: dict[str, str] = {}
    call_id_to_name: dict[str, str] = {}
    reasoning_buf: list[str] = []
    thinking_buf: list[str] = []
    cumulative_context_chars: int = 0
    last_model_response: Any = None

    model_settings = _build_model_settings(state)

    async def _human_input_callback(
        message: str,
        input_fields: list[dict] | None = None,
        info_blocks: list[dict] | None = None,
        upcoming_actions: list[dict] | None = None,
    ) -> None:
        await _safe_send(ws, _evt("human_input_requested", {
            "run_id": run.run_id,
            "session_id": session_id,
            "message": message,
            "input_fields": input_fields,
            "info_blocks": info_blocks,
            "upcoming_actions": upcoming_actions,
        }))

    async def _robot_event_cb(event: dict) -> None:
        current_step_id = state.deps.state.get("_current_step_id", "")
        await _safe_send(ws, _evt("robot_event", {
            "step_id": current_step_id,
            "robot_step": event.get("step", 0),
            "name": event.get("name", ""),
            "message": event.get("message", ""),
        }))

    state.deps.state["_human_input_callback"] = _human_input_callback
    state.deps.state["_cancel_event"] = cancel_event
    state.deps.state["_robot_event_callback"] = _robot_event_cb

    await _safe_send(ws, _evt("run_start", {
        "run_id": run.run_id,
        "session_id": session_id,
        "query": query,
        "provider": state.provider,
        "resume": is_resume,
        "resumed_from_step": len(run.steps) if is_resume else 0,
    }))

    _persist_session(state, session_data, run)

    max_steps = state.config.agent.max_iterations
    try:
        async for event in cell_culture_agent.run_stream_events(
            query, deps=state.deps, model=state.model,
            model_settings=model_settings,
            message_history=message_history or [],
            usage_limits=UsageLimits(request_limit=max_steps),
        ):
            if cancel_event.is_set():
                run.stop()
                _persist_session(state, session_data, run)
                await _safe_send(ws, _evt("run_stopped", {
                    "run_id": run.run_id,
                    "session_id": session_id,
                    "step_count": len(run.steps),
                    "duration_ms": run.duration_ms,
                }))
                return

            if isinstance(event, PartStartEvent):
                if isinstance(event.part, TextPart) and event.part.content:
                    run.content_chunks.append(event.part.content)
                    reasoning_buf.append(event.part.content)
                    await _safe_send(ws, _evt("content_delta", {
                        "delta": event.part.content,
                    }))
                elif isinstance(event.part, ThinkingPart) and event.part.content:
                    run.thinking_chunks.append(event.part.content)
                    thinking_buf.append(event.part.content)
                    await _safe_send(ws, _evt("thinking_delta", {
                        "delta": event.part.content,
                    }))

            elif isinstance(event, PartDeltaEvent):
                if isinstance(event.delta, TextPartDelta) and event.delta.content_delta:
                    run.content_chunks.append(event.delta.content_delta)
                    reasoning_buf.append(event.delta.content_delta)
                    await _safe_send(ws, _evt("content_delta", {
                        "delta": event.delta.content_delta,
                    }))
                elif isinstance(event.delta, ThinkingPartDelta) and event.delta.content_delta:
                    run.thinking_chunks.append(event.delta.content_delta)
                    thinking_buf.append(event.delta.content_delta)
                    await _safe_send(ws, _evt("thinking_delta", {
                        "delta": event.delta.content_delta,
                    }))

            elif isinstance(event, FunctionToolCallEvent):
                state.total_tool_calls += 1
                call_id = event.part.tool_call_id or ""
                args = _parse_args(event.part.args)

                reasoning_text = "".join(reasoning_buf).strip()
                thinking_text = "".join(thinking_buf).strip()
                reasoning_buf.clear()
                thinking_buf.clear()

                step = run.add_step(
                    event.part.tool_name, args,
                    reasoning=reasoning_text or None,
                    thinking=thinking_text or None,
                )

                step_chars = (
                    len(json.dumps(reasoning_text or ""))
                    + len(json.dumps(args))
                )
                cumulative_context_chars += step_chars
                step.context_chars = step_chars
                step.cumulative_context_chars = cumulative_context_chars
                step.context_messages = 2 * step.step_number + 1

                llm_usage = get_last_usage()
                if llm_usage.get("usage"):
                    step.prompt_tokens = llm_usage["usage"].get("prompt_tokens")
                    step.completion_tokens = llm_usage["usage"].get("completion_tokens")
                    step.total_tokens = llm_usage["usage"].get("total_tokens")
                if llm_usage.get("context_chars"):
                    step.context_chars = llm_usage["context_chars"]
                    step.context_messages = llm_usage.get("message_count", step.context_messages)

                call_id_to_step[call_id] = step.id
                call_id_to_name[call_id] = event.part.tool_name
                state.deps.state["_current_step_id"] = step.id

                await _safe_send(ws, _evt("step_start", {
                    "step_id": step.id,
                    "step_number": step.step_number,
                    "tool_name": event.part.tool_name,
                    "arguments": args,
                    "reasoning": reasoning_text or None,
                    "thinking": thinking_text or None,
                    "context_chars": step.cumulative_context_chars,
                }))

                _persist_session(state, session_data, run)

            elif isinstance(event, FunctionToolResultEvent):
                call_id = event.tool_call_id or ""
                step_id = call_id_to_step.get(call_id, "")
                tool_name = event.result.tool_name or call_id_to_name.get(call_id, "")
                raw = event.result.content
                content = _serialize_content(raw)

                run.complete_step(step_id, raw)

                result_chars = len(content)
                cumulative_context_chars += result_chars

                step = next((s for s in run.steps if s.id == step_id), None)
                if step:
                    step.cumulative_context_chars = cumulative_context_chars

                await _safe_send(ws, _evt("step_complete", {
                    "step_id": step_id,
                    "step_number": step.step_number if step else 0,
                    "tool_name": tool_name,
                    "result": content,
                    "duration_ms": step.duration_ms if step else None,
                    "cumulative_context_chars": cumulative_context_chars,
                }))

                _persist_session(state, session_data, run)

            elif isinstance(event, AgentRunResultEvent):
                result_obj = event.result.output
                output_data = result_obj.model_dump() if hasattr(result_obj, "model_dump") else {"summary": str(result_obj)}
                output = output_data.get("summary", str(result_obj))

                run.finish(output)
                _persist_session(state, session_data, run)

                total_prompt_tokens = sum(s.prompt_tokens or 0 for s in run.steps)
                total_completion_tokens = sum(s.completion_tokens or 0 for s in run.steps)

                await _safe_send(ws, _evt("run_complete", {
                    "run_id": run.run_id,
                    "session_id": session_id,
                    "step_count": len(run.steps),
                    "duration_ms": run.duration_ms,
                    "completion": output_data,
                    "final_context_chars": cumulative_context_chars,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                }))

    except UsageLimitExceeded:
        LOG.warning("Max steps (%d) reached for run %s", max_steps, run.run_id)
        run.finish(f"Reached maximum step budget ({max_steps}). Stopping.")
        _persist_session(state, session_data, run)
        await _safe_send(ws, _evt("run_complete", {
            "run_id": run.run_id,
            "session_id": session_id,
            "step_count": len(run.steps),
            "duration_ms": run.duration_ms,
            "budget_exhausted": True,
        }))
    except asyncio.CancelledError:
        run.stop()
        _persist_session(state, session_data, run)
        await _safe_send(ws, _evt("run_stopped", {
            "run_id": run.run_id,
            "session_id": session_id,
            "step_count": len(run.steps),
            "duration_ms": run.duration_ms,
        }))
    finally:
        state.deps.state.pop("_human_input_callback", None)
        state.deps.state.pop("_human_input_future", None)
        state.deps.state.pop("_cancel_event", None)
        state.deps.state.pop("_robot_event_callback", None)
        state.deps.state.pop("_current_step_id", None)


# ── REST ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict[str, Any]:
    state = _get_state()
    return {"status": "ok", **state.snapshot()}


@app.get("/api/tools")
async def list_tools_endpoint() -> dict[str, Any]:
    """Return tool names+descriptions and full JSON schemas the LLM receives."""
    tools = cell_culture_agent._function_toolset.tools
    tool_list = []
    for name, tool in tools.items():
        td = tool.tool_def
        tool_list.append({
            "name": name,
            "description": td.description,
            "parameters_schema": td.parameters_json_schema,
        })

    return {
        "tools": tool_list,
        "total": len(tool_list),
    }


@app.get("/api/agent-schema")
async def agent_schema_endpoint() -> dict[str, Any]:
    """Debug: the complete constant context sent to the LLM on every call.

    System prompt + tool schemas are CONSTANT (defined at agent creation).
    The DYNAMIC part is the conversation context: user query + accumulated
    tool call/result history within the current run.
    """
    tools = cell_culture_agent._function_toolset.tools
    tool_schemas = []
    for name, tool in tools.items():
        td = tool.tool_def
        tool_schemas.append({
            "name": name,
            "description": td.description,
            "parameters": td.parameters_json_schema,
        })

    system_prompt = ""
    if cell_culture_agent._system_prompts:
        sp = cell_culture_agent._system_prompts[0]
        system_prompt = sp if isinstance(sp, str) else str(sp)

    state = _get_state()
    return {
        "provider": state.provider,
        "model": state.config.llm.get_provider(state.provider).model,
        "mock_mode": state.config.tools.mock_mode,
        "system_prompt": system_prompt,
        "tools": tool_schemas,
        "tool_count": len(tool_schemas),
        "model_settings": _build_model_settings(state),
    }


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    state = _get_state()
    return state.config.model_dump()


@app.get("/api/sessions")
async def list_sessions_endpoint() -> dict[str, Any]:
    return {"sessions": list_sessions()}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    data = load_session(session_id)
    if not data:
        return {"error": f"Session '{session_id}' not found"}
    return data


@app.post("/api/sessions")
async def create_session_endpoint() -> dict[str, Any]:
    session_id = uuid.uuid4().hex[:12]
    data = create_session_file(session_id)
    return data


# ── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    state = _get_state()
    ws_id = uuid.uuid4().hex[:12]
    state.active_sessions[ws_id] = {"status": "connected"}
    LOG.info("WS session %s connected", ws_id)

    run_task: asyncio.Task | None = None
    cancel_event = asyncio.Event()

    async def _cancel_current() -> None:
        nonlocal run_task
        if run_task and not run_task.done():
            cancel_event.set()
            try:
                await asyncio.wait_for(run_task, timeout=5.0)
            except asyncio.TimeoutError:
                run_task.cancel()

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json(_evt("error", {"error": "Invalid JSON"}))
                continue

            action = msg.get("action")

            if action == "stop":
                await _cancel_current()
                continue

            if action == "human_response":
                future = state.deps.state.get("_human_input_future")
                if future and not future.done():
                    future.set_result(msg.get("response", ""))
                continue

            if action == "resume":
                session_id = msg.get("session_id")
                if not session_id:
                    await ws.send_json(_evt("error", {"error": "Missing session_id"}))
                    continue

                session_data = load_session(session_id)
                if not session_data:
                    await ws.send_json(_evt("error", {"error": "Session not found"}))
                    continue

                runs = session_data.get("runs", [])
                stopped_run = None
                for r in reversed(runs):
                    if r.get("status") == "stopped":
                        stopped_run = r
                        break

                if not stopped_run:
                    await ws.send_json(_evt("error", {"error": "No stopped run to resume"}))
                    continue

                await _cancel_current()
                cancel_event.clear()
                state.active_sessions[ws_id]["status"] = "running"

                completed_steps = [s for s in stopped_run.get("steps", []) if s["status"] == "completed"]
                query = stopped_run["query"]
                msg_history = _reconstruct_message_history(query, completed_steps)
                rebuilt_run = _rebuild_run_from_stopped(stopped_run)

                _rebuild_mock_world_from_steps(state, completed_steps)

                await _safe_send(ws, _evt("session_history", {
                    "session_id": session_id,
                    "runs": runs,
                }))

                run_task = asyncio.create_task(
                    _run_with_error_handling(
                        ws, query, session_id, cancel_event, ws_id,
                        message_history=msg_history,
                        existing_run=rebuilt_run,
                        is_resume=True,
                    )
                )
                continue

            query = msg.get("query", "").strip()
            if not query:
                await ws.send_json(_evt("error", {"error": "Empty query"}))
                continue

            session_id = msg.get("session_id") or uuid.uuid4().hex[:12]

            await _cancel_current()
            cancel_event.clear()
            state.active_sessions[ws_id]["status"] = "running"

            run_task = asyncio.create_task(
                _run_with_error_handling(ws, query, session_id, cancel_event, ws_id)
            )

    except WebSocketDisconnect:
        LOG.info("WS session %s disconnected", ws_id)
        cancel_event.set()
        if run_task and not run_task.done():
            run_task.cancel()
    finally:
        state.active_sessions.pop(ws_id, None)


async def _run_with_error_handling(
    ws: WebSocket,
    query: str,
    session_id: str,
    cancel_event: asyncio.Event,
    ws_id: str,
    *,
    message_history: list[ModelMessage] | None = None,
    existing_run: RunMemory | None = None,
    is_resume: bool = False,
) -> None:
    state = _get_state()
    try:
        await _stream_to_ws(
            ws, query, session_id, cancel_event,
            message_history=message_history,
            existing_run=existing_run,
            is_resume=is_resume,
        )
    except Exception as exc:
        LOG.error("Agent error in WS %s: %s", ws_id, exc, exc_info=True)
        await _safe_send(ws, _evt("error", {
            "error": str(exc),
            "type": type(exc).__name__,
        }))
    finally:
        sess = state.active_sessions.get(ws_id)
        if sess is not None:
            sess["status"] = "idle"
