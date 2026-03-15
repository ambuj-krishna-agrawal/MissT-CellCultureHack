"""Flask capping operations — decap and recap at the Capping Station.

The capping station is a dedicated fixture that grips the flask body
while a motorised head unscrews (decap) or screws on (recap) the cap.
Flask must be at Capping_Station before calling these tools.
"""

from __future__ import annotations

import uuid

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def run_decap(
    ctx: RunContext[AgentDeps],
    flask_id: str,
) -> dict:
    """Remove the cap from a flask at the Capping Station.

    Flask must already be positioned at the Capping Station via pick_and_place.
    After decapping, the flask is open for pipette operations.

    Args:
        flask_id: Flask to decap (e.g. "flask_1").
    """
    if ctx.deps.mock_mode:
        from agent.core.robot_stream import drain_robot_if_active
        drained = await drain_robot_if_active(ctx.deps, "run_decap")
        if not drained:
            await ctx.deps.mock_pause()
        return {
            "action": "run_decap",
            "flask_id": flask_id,
            "success": True,
            "cap_status": "removed",
            "duration_s": 4.2,
            "operation_id": f"decap_{uuid.uuid4().hex[:8]}",
            "message": f"Cap removed from {flask_id} at Capping Station",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live capping station not connected.")


async def run_recap(
    ctx: RunContext[AgentDeps],
    flask_id: str,
) -> dict:
    """Replace the cap on a flask at the Capping Station.

    Flask must be at the Capping Station. After recapping, the flask is
    sealed with a vented cap for CO₂ exchange during incubation.

    Args:
        flask_id: Flask to recap (e.g. "flask_1").
    """
    if ctx.deps.mock_mode:
        from agent.core.robot_stream import drain_robot_if_active
        drained = await drain_robot_if_active(ctx.deps, "run_recap")
        if not drained:
            await ctx.deps.mock_pause()
        return {
            "action": "run_recap",
            "flask_id": flask_id,
            "success": True,
            "cap_status": "sealed",
            "cap_type": "vented",
            "duration_s": 4.5,
            "operation_id": f"recap_{uuid.uuid4().hex[:8]}",
            "message": f"Cap replaced on {flask_id} (vented cap, sealed)",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live capping station not connected.")
