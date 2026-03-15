"""
Path planner for UR + RTDE that reduces singularity risk by:
1. Using a single fixed orientation (wrist 3 horizontal / parallel to ground) for all poses.
2. Moving via waypoints: lift to safe height → move XY → lower to target (no straight-line
   Cartesian move through singular configurations).
"""
from __future__ import annotations

from typing import List, Sequence

# Default orientation (rx, ry, rz in rad) that keeps wrist 3 horizontal (axis parallel to ground).
# Use one consistent orientation for all work poses to avoid wrist flip singularities.
# Tune to match your cell: e.g. [0.008, -2.123, 2.269] for your current poses.
WRIST3_HORIZONTAL_ORIENTATION = [0.008, -2.123, 2.269]  # (rx, ry, rz)


def apply_fixed_orientation(pose: Sequence[float], orientation: Sequence[float] | None = None) -> List[float]:
    """Return [x, y, z, rx, ry, rz] with pose position but fixed orientation (wrist 3 horizontal)."""
    orient = list(orientation) if orientation is not None else list(WRIST3_HORIZONTAL_ORIENTATION)
    return [float(pose[0]), float(pose[1]), float(pose[2]), orient[0], orient[1], orient[2]]


def plan_linear_path(
    start_pose: Sequence[float],
    end_pose: Sequence[float],
    fixed_orientation: Sequence[float] | None = None,
    safe_height: float | None = None,
    min_lift_height: float = 0.45,
) -> List[List[float]]:
    """
    Plan a path from start to end that avoids straight-line singularity-prone moves.

    - All waypoints use fixed_orientation (wrist 3 horizontal).
    - If safe_height is set (or derived from min_lift_height): path is
      start → lift to safe_z → move (x,y) at safe_z → lower to end.
    - If safe_height is None and both poses have z >= min_lift_height, returns
      [start_with_orient, end_with_orient] (no intermediate lift).

    Returns list of 6D poses [x, y, z, rx, ry, rz] for moveL sequence.
    """
    orient = list(fixed_orientation) if fixed_orientation is not None else list(WRIST3_HORIZONTAL_ORIENTATION)
    start = apply_fixed_orientation(start_pose, orient)
    end = apply_fixed_orientation(end_pose, orient)

    z_start = start[2]
    z_end = end[2]
    safe_z = safe_height if safe_height is not None else max(min_lift_height, z_start, z_end) + 0.05

    waypoints: List[List[float]] = []
    waypoints.append(start)
    # Lift to safe height (same x, y)
    waypoints.append([start[0], start[1], safe_z, orient[0], orient[1], orient[2]])
    # Move to above end at safe height
    waypoints.append([end[0], end[1], safe_z, orient[0], orient[1], orient[2]])
    # Lower to end
    waypoints.append(end)
    return waypoints


def moveL_path(rtde_c, waypoints: List[List[float]], speed: float, accel: float) -> bool:
    """Execute a sequence of moveL commands. Returns True if all succeeded."""
    for pose in waypoints:
        ok = rtde_c.moveL(pose, speed, accel)
        if not ok:
            return False
    return True


def moveL_planned(
    rtde_c,
    rtde_r,
    end_pose: Sequence[float],
    speed: float,
    accel: float,
    fixed_orientation: Sequence[float] | None = None,
    safe_height: float | None = 0.5,
    min_lift_height: float = 0.45,
) -> bool:
    """
    Move from current TCP pose to end_pose using a planned path (lift → move XY → lower)
    with fixed orientation (wrist 3 horizontal). Use this instead of a single moveL
    to reduce singularity risk.
    """
    start_pose = list(rtde_r.getActualTCPPose())
    waypoints = plan_linear_path(
        start_pose,
        end_pose,
        fixed_orientation=fixed_orientation,
        safe_height=safe_height,
        min_lift_height=min_lift_height,
    )
    return moveL_path(rtde_c, waypoints, speed, accel)


def moveL_planned_or_direct(
    rtde_c,
    rtde_r,
    end_pose: Sequence[float],
    speed: float,
    accel: float,
    fixed_orientation: Sequence[float] | None = None,
    safe_height: float | None = 0.5,
    use_planned_path: bool = True,
) -> bool:
    """
    If use_planned_path: move via plan (lift → move → lower) with fixed orientation.
    Else: single moveL with fixed orientation applied to end_pose.
    """
    end = apply_fixed_orientation(end_pose, fixed_orientation)
    if use_planned_path and safe_height is not None:
        return moveL_planned(
            rtde_c, rtde_r, end, speed, accel,
            fixed_orientation=fixed_orientation,
            safe_height=safe_height,
        )
    return rtde_c.moveL(end, speed, accel)
