"""Flask lifecycle operations — disposal and cell collection.

These tools handle end-of-life flask operations:
  dispose_flask: discard a used flask to the waste bin
  collect_cells: transfer cell suspension from flask into a falcon tube
"""

from __future__ import annotations

import uuid

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def dispose_flask(
    ctx: RunContext[AgentDeps],
    flask_id: str,
    reason: str = "experiment_complete",
) -> dict:
    """Dispose of a used flask into the waste bin.

    The robot picks up the flask and places it into the biohazard waste.
    Flask should be capped before disposal for biosafety.

    Args:
        flask_id: Flask to dispose (e.g. "flask_1").
        reason: Why the flask is being disposed. One of:
            "experiment_complete", "contamination_detected", "dissociation_declined".
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        return {
            "action": "dispose_flask",
            "flask_id": flask_id,
            "reason": reason,
            "success": True,
            "destination": "biohazard_waste",
            "duration_s": 8.3,
            "operation_id": f"dispose_{uuid.uuid4().hex[:8]}",
            "message": f"Flask {flask_id} disposed to biohazard waste (reason: {reason})",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live flask disposal requires robot connection.")


async def collect_cells(
    ctx: RunContext[AgentDeps],
    flask_id: str,
    target_container: str = "falcon_50mL",
    volume_mL: float = 10.0,
) -> dict:
    """Collect cell suspension from flask into a collection vessel.

    Aspirates the cell suspension (cells + media/enzyme) from the flask
    and transfers it to a falcon tube. Reports cell count and viability.

    Args:
        flask_id: Flask containing the cell suspension.
        target_container: Collection vessel (e.g. "falcon_50mL").
        volume_mL: Volume to collect in millilitres.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        ctx.deps.set_culture_phase("harvested")

        cell_count = 6_200_000
        viability_pct = 95.5
        efficiency_pct = 96.9

        return {
            "action": "collect_cells",
            "flask_id": flask_id,
            "target_container": target_container,
            "volume_mL": volume_mL,
            "success": True,
            "cell_count": cell_count,
            "cell_count_formatted": f"{cell_count / 1_000_000:.1f}M",
            "viability_pct": viability_pct,
            "efficiency_pct": efficiency_pct,
            "duration_s": 15.2,
            "operation_id": f"collect_{uuid.uuid4().hex[:8]}",
            "message": (
                f"Collected {volume_mL} mL cell suspension into {target_container}. "
                f"Cell count: {cell_count / 1_000_000:.1f}M, "
                f"Viability: {viability_pct}%, Efficiency: {efficiency_pct}%"
            ),
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live cell collection requires liquid handling hardware.")
