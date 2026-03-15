"""Camera and perception tools — bench verification and microscopy."""

from __future__ import annotations

import uuid

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def capture_image(
    ctx: RunContext[AgentDeps],
    purpose: str,
    camera_id: str = "zebra_main",
    mode: str = "visual",
) -> dict:
    """Capture an image from the camera system.

    Args:
        purpose: What you are looking for (e.g. "verify flask positions", "cell count monitoring").
        camera_id: Camera identifier. "zebra_main" for bench, "microscope" for cell imaging.
        mode: Capture mode — "visual" for bench verification, "microscopy" for cell imaging.
    """
    if ctx.deps.mock_mode:
        from agent.core.robot_stream import drain_robot_if_active
        drained = await drain_robot_if_active(ctx.deps, "capture_image")
        if not drained:
            await ctx.deps.mock_pause()
        image_id = f"img_{uuid.uuid4().hex[:8]}"
        day = ctx.deps.protocol_day

        from agent.providers.scenarios import load_scenario
        scenario = load_scenario(ctx.deps.mock_scenario)
        image_url = scenario.get_image_url(day)

        if mode == "microscopy":
            return {
                "image_id": image_id,
                "camera_id": camera_id,
                "mode": "microscopy",
                "magnification": "40x",
                "resolution": {"width": 2048, "height": 2048},
                "format": "16-bit grayscale",
                "purpose": purpose,
                "illumination": "brightfield",
                "timestamp": "2026-03-13T19:30:00Z",
                "status": "captured",
                "protocol_day": day,
                "image_url": image_url,
            }

        return {
            "image_id": image_id,
            "camera_id": camera_id,
            "mode": "visual",
            "resolution": {"width": 2592, "height": 1944},
            "format": "RGB",
            "purpose": purpose,
            "timestamp": "2026-03-13T18:00:00Z",
            "status": "captured",
            "protocol_day": day,
        }

    raise NotImplementedError(
        f"Camera at {ctx.deps.camera_host}:{ctx.deps.camera_port} not connected."
    )
