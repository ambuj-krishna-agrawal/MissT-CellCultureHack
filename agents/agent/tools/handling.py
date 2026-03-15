"""Mechanical handling tool — apply fast or gentle agitation for cell detachment."""

from __future__ import annotations

import uuid

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def apply_handling(
    ctx: RunContext[AgentDeps],
    flask_id: str,
    mode: str = "fast",
    duration_seconds: int = 10,
) -> dict:
    """Apply mechanical handling to detach cells after dissociation reagent incubation.

    For iPSC passaging with TrypLE: after enzyme incubation, shake/agitate the
    flask to dislodge detached cells. "fast" mode uses firm tapping; "gentle"
    mode uses light rocking.

    Args:
        flask_id: The flask to apply handling to.
        mode: Handling mode — "fast" (firm tapping, quicker detachment) or "gentle" (light rocking, larger aggregates).
        duration_seconds: Duration of mechanical agitation in seconds.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        ctx.deps.set_culture_phase("suspended")

        detachment_pct = 95.0 if mode == "fast" else 80.0
        aggregate_size = "50–150 µm" if mode == "fast" else "100–200 µm"

        method = "firm tapping (5–8 sharp taps)" if mode == "fast" else "gentle rocking (30s slow tilts)"

        return {
            "action": "apply_handling",
            "flask_id": flask_id,
            "mode": mode,
            "duration_seconds": duration_seconds,
            "method": method,
            "success": True,
            "detachment_estimate": f"~{detachment_pct}% cells detached",
            "aggregate_size_range": aggregate_size,
            "motion_id": f"handling_{uuid.uuid4().hex[:8]}",
            "message": (
                f"Applied {mode} handling to {flask_id} for {duration_seconds}s. "
                f"Estimated {detachment_pct}% cell detachment. "
                f"Aggregate size: {aggregate_size}."
            ),
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live handling requires robot motion controller.")
