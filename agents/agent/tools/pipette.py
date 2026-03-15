"""Individual pipette operations — aspirate and dispense.

Split from the combined pipette_transfer for finer-grained robot control:
  pipette_aspirate: remove liquid from flask → waste
  pipette_add: dispense reagent into flask from source reservoir
"""

from __future__ import annotations

import uuid

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def pipette_aspirate(
    ctx: RunContext[AgentDeps],
    flask_id: str,
    reagent: str,
    volume_mL: float,
) -> dict:
    """Aspirate liquid from a flask and discard to waste.

    Used for removing spent media, DPBS wash, or any liquid that needs
    to be discarded before adding fresh reagent.

    Args:
        flask_id: Flask to aspirate from (e.g. "flask_1").
        reagent: What is being removed (e.g. "spent_media", "DPBS_wash").
        volume_mL: Volume to aspirate in millilitres.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        return {
            "action": "pipette_aspirate",
            "flask_id": flask_id,
            "reagent": reagent,
            "volume_mL": volume_mL,
            "destination": "waste",
            "success": True,
            "duration_s": round(2.5 + volume_mL * 0.1, 1),
            "operation_id": f"asp_{uuid.uuid4().hex[:8]}",
            "message": f"Aspirated {volume_mL} mL {reagent} from {flask_id} → waste",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live pipette requires liquid handling hardware.")


async def pipette_add(
    ctx: RunContext[AgentDeps],
    flask_id: str,
    reagent: str,
    volume_mL: float,
    source: str,
) -> dict:
    """Dispense reagent into a flask from a source reservoir.

    Gently dispenses against the flask wall to avoid disturbing the cell
    monolayer (for media) or ensures full surface coverage (for enzyme).

    Args:
        flask_id: Target flask (e.g. "flask_1").
        reagent: Reagent name (e.g. "Media_A", "TrypLE", "DPBS").
        volume_mL: Volume to dispense in millilitres.
        source: Source reservoir or bottle ID (e.g. "media_a_reservoir", "tryple_bottle").
    """
    if ctx.deps.mock_mode:
        from agent.core.robot_stream import drain_robot_if_active
        drained = await drain_robot_if_active(ctx.deps, "pipette_add")
        if not drained:
            await ctx.deps.mock_pause()
        # TrypLE addition transitions culture from growing → dissociating
        if "tryple" in reagent.lower():
            ctx.deps.set_culture_phase("dissociating")
        return {
            "action": "pipette_add",
            "flask_id": flask_id,
            "reagent": reagent,
            "volume_mL": volume_mL,
            "source": source,
            "success": True,
            "duration_s": round(2.0 + volume_mL * 0.1, 1),
            "operation_id": f"add_{uuid.uuid4().hex[:8]}",
            "message": f"Dispensed {volume_mL} mL {reagent} into {flask_id} from {source}",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live pipette requires liquid handling hardware.")
