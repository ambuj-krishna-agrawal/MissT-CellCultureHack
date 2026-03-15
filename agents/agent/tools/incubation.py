"""Incubation control tool — configure temperature, CO₂, and duration for iPSC culture."""

from __future__ import annotations

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def set_incubation(
    ctx: RunContext[AgentDeps],
    flask_id: str,
    temperature_c: float = 37.0,
    co2_pct: float = 5.0,
    duration_minutes: int = 0,
    mode: str = "continuous",
) -> dict:
    """Configure and start incubation for a flask.

    Args:
        flask_id: The flask to incubate.
        temperature_c: Target temperature in Celsius (iPSC optimal: 37°C).
        co2_pct: CO₂ percentage (iPSC optimal: 5%).
        duration_minutes: Duration in minutes. 0 = continuous until manually stopped. Use 5–7 for TrypLE dissociation.
        mode: "continuous" for ongoing culture, "timed" for dissociation incubation.
    """
    if ctx.deps.mock_mode:
        from agent.core.robot_stream import drain_robot_if_active
        drained = await drain_robot_if_active(ctx.deps, "set_incubation")
        if not drained:
            await ctx.deps.mock_pause()
        # Overnight/continuous incubation advances the protocol day
        if duration_minutes == 0 or mode == "continuous":
            ctx.deps.advance_protocol_day()
        return {
            "flask_id": flask_id,
            "status": "incubating",
            "temperature_c": temperature_c,
            "actual_temperature_c": temperature_c + 0.1,
            "co2_pct": co2_pct,
            "humidity_pct": 95.0,
            "duration_minutes": duration_minutes,
            "mode": mode,
            "incubator_slot": "Incubator_Slot_A",
            "started": True,
            "protocol_day": ctx.deps.protocol_day,
            "message": (
                f"Incubation started: {temperature_c}°C, {co2_pct}% CO₂, "
                f"{'continuous' if mode == 'continuous' else f'{duration_minutes} min timed'}"
            ),
        }

    raise NotImplementedError("Live incubator control requires hardware connection.")
