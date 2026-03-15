"""Robot service tools — poses, pick-and-place, liquid handling.

Interfaces with UR12e (6-axis, IP54) via ROS.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def get_robot_poses(ctx: RunContext[AgentDeps], components: list[str]) -> dict:
    """Query current robot state: joint positions, end-effector pose, gripper status.

    Args:
        components: Which components to query. Options: joints, end_effector, gripper.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        data: dict = {"robot_model": "UR12e", "enclosure": "IP54"}
        if "joints" in components:
            data["joints"] = {
                "shoulder_pan": 0.0, "shoulder_lift": -1.5708,
                "elbow": 1.5708, "wrist_1": -1.5708,
                "wrist_2": -1.5708, "wrist_3": 0.0, "unit": "radians",
            }
        if "end_effector" in components:
            data["end_effector"] = {
                "position": {"x": 0.5, "y": 0.0, "z": 0.5},
                "orientation": {"qx": 0.0, "qy": 1.0, "qz": 0.0, "qw": 0.0},
                "frame": "base_link",
            }
        if "gripper" in components:
            data["gripper"] = {
                "position_mm": 85.0, "force_n": 0.0,
                "holding": False, "object_detected": False,
            }
        data["status"] = "idle"
        data["protocol_day"] = ctx.deps.protocol_day
        return data

    raise NotImplementedError(f"Live robot at {ctx.deps.robot_host}:{ctx.deps.robot_port} not configured.")


async def get_station_poses(ctx: RunContext[AgentDeps], station_names: list[str] | None = None) -> dict:
    """Query poses of workcell stations (incubator, microscope, BSC, etc).

    Args:
        station_names: Station names to query. Pass empty list or omit for all stations.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        all_stations = {
            "Flask_Storage": {"frame": "base_link", "pose": {"x": 0.4, "y": -0.5, "z": 0.35}, "approach_offset_z": 0.08},
            "Incubator_Slot_A": {"frame": "base_link", "pose": {"x": 1.0, "y": -0.35, "z": 0.35}, "approach_offset_z": 0.08},
            "BSC_1": {"frame": "base_link", "pose": {"x": 0.8, "y": -0.5, "z": 0.4}, "approach_offset_z": 0.1},
            "Microscope_Stage": {"frame": "base_link", "pose": {"x": 1.0, "y": 0.35, "z": 0.35}, "approach_offset_z": 0.08},
            "Pipette_Station": {"frame": "base_link", "pose": {"x": 0.6, "y": 0.3, "z": 0.35}, "approach_offset_z": 0.05},
            "Shaker_Platform": {"frame": "base_link", "pose": {"x": 0.7, "y": 0.0, "z": 0.35}, "approach_offset_z": 0.06},
            "Capping_Station": {"frame": "base_link", "pose": {"x": 0.5, "y": -0.3, "z": 0.38}, "approach_offset_z": 0.06},
            "Feeding_Station": {"frame": "base_link", "pose": {"x": 0.6, "y": -0.3, "z": 0.35}, "approach_offset_z": 0.05},
            "Harvest_Station": {"frame": "base_link", "pose": {"x": 0.8, "y": -0.3, "z": 0.35}, "approach_offset_z": 0.05},
        }
        if station_names:
            return {"stations": {n: all_stations.get(n, {"error": f"Unknown: {n}"}) for n in station_names}, "protocol_day": ctx.deps.protocol_day}
        return {"stations": all_stations, "protocol_day": ctx.deps.protocol_day}

    raise NotImplementedError("Live station service not configured.")


async def pick_and_place(
    ctx: RunContext[AgentDeps],
    object_id: str,
    from_station: str,
    to_station: str,
) -> dict:
    """Pick an object from one station and place it at another.

    The robot will: approach → grip → lift → transfer → lower → release.
    Verifies gripper grasp before moving.

    Args:
        object_id: ID of the object to move (e.g. "flask_1").
        from_station: Source station name.
        to_station: Destination station name.
    """
    if ctx.deps.mock_mode:
        from agent.core.robot_stream import drain_robot_if_active, maybe_start_robot_stream
        if "incubator" in from_station.lower() and "microscope" in to_station.lower():
            maybe_start_robot_stream(ctx.deps)
        drained = await drain_robot_if_active(ctx.deps, "pick_and_place")
        if not drained:
            await ctx.deps.mock_pause()
        return {
            "action": "pick_and_place",
            "object_id": object_id,
            "from_station": from_station,
            "to_station": to_station,
            "success": True,
            "grasp_verified": True,
            "duration_s": 12.4,
            "motion_id": f"motion_{uuid.uuid4().hex[:8]}",
            "message": f"Moved {object_id}: {from_station} → {to_station}",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live robot pick-and-place requires ROS 2 MoveIt connection.")


async def pipette_transfer(
    ctx: RunContext[AgentDeps],
    transfers: list[dict[str, Any]],
    flask_id: str,
) -> dict:
    """Execute one or more liquid transfers using the pipette station.

    Each transfer specifies a reagent, volume, and source. The robot will
    aspirate from the source and dispense into the target flask.

    Args:
        transfers: List of transfer steps. Each dict has:
            reagent (str), volume_uL (float), source (str).
        flask_id: Target flask receiving the liquids.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        results: list[dict[str, Any]] = []
        total_vol = 0.0
        for t in transfers:
            vol = float(t.get("volume_uL", 0))
            total_vol += vol
            results.append({
                "reagent": t.get("reagent", "unknown"),
                "volume_uL": vol,
                "source": t.get("source", "unknown"),
                "status": "dispensed",
            })

        return {
            "action": "pipette_transfer",
            "flask_id": flask_id,
            "transfers": results,
            "total_volume_uL": round(total_vol, 2),
            "transfer_count": len(results),
            "success": True,
            "message": f"Dispensed {round(total_vol, 1)} µL into {flask_id} ({len(results)} transfers)",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live pipette requires liquid handling hardware.")
