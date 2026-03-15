"""Execution plan tools — generate and load phase-specific plans.

generate_execution_plan: After user approves the protocol, the LLM generates
  a detailed execution plan covering all phases. This is stored in memory
  and referenced throughout execution.

load_phase_plan: At the start of each execution phase, loads the relevant
  steps from the stored plan so the LLM can follow them precisely.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


_PLAN_PATH = Path(__file__).parent.parent / "providers" / "execution_plan.json"


def _find_phase(plan: dict, phase_id: str) -> dict:
    """Look up a phase by id from the phases array."""
    for p in plan.get("phases", []):
        if p.get("id") == phase_id:
            return p
    return {}


async def generate_execution_plan(
    ctx: RunContext[AgentDeps],
    protocol_summary: str,
) -> dict:
    """Generate a detailed execution plan for the approved protocol.

    Call this ONCE after the scientist approves the protocol plan.
    Produces a phase-by-phase breakdown of every step the robot will execute,
    including tool calls, arguments, timing, and decision points.

    The plan is stored in agent memory for phase-by-phase execution.

    Args:
        protocol_summary: Brief description of the approved protocol
            (cell line, labware, density, target, dissociation method).
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()

        plan = json.loads(_PLAN_PATH.read_text())
        ctx.deps.state["execution_plan"] = plan

        phases = plan.get("phases", [])
        phase_names = [p.get("name", p.get("id", "?")) for p in phases]
        total_steps = sum(len(p.get("steps", [])) for p in phases)
        schedule = plan.get("schedule", {})

        return {
            "action": "generate_execution_plan",
            "success": True,
            "protocol_summary": protocol_summary,
            "total_phases": len(phases),
            "total_steps": total_steps,
            "phase_names": phase_names,
            "schedule": schedule,
            "message": (
                f"Execution plan generated: {total_steps} steps across "
                f"{len(phases)} phases. Plan stored in memory."
            ),
        }

    raise NotImplementedError("Live execution plan generation requires LLM call.")


async def load_phase_plan(
    ctx: RunContext[AgentDeps],
    phase: str,
) -> dict:
    """Load execution steps for a specific phase from the stored plan.

    Call at the START of each execution phase to load the relevant steps
    into context. The steps guide tool selection and argument values.

    Args:
        phase: Which phase to load. One of: "phase_2", "phase_3".
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()

        plan = ctx.deps.state.get("execution_plan", {})
        phase_data = _find_phase(plan, phase)
        steps = phase_data.get("steps", [])

        step_summaries = []
        for s in steps:
            step_summaries.append({
                "id": s.get("id"),
                "what": s.get("what"),
                "tool": s.get("how", {}).get("tool", "—"),
            })

        return {
            "action": "load_phase_plan",
            "phase": phase,
            "phase_name": phase_data.get("name", phase),
            "step_count": len(steps),
            "steps": step_summaries,
            "success": True,
            "message": (
                f"Loaded {len(steps)} steps for {phase_data.get('name', phase)}. "
                f"Follow these steps in order."
            ),
        }

    raise NotImplementedError("Live phase plan loading requires stored plan.")
