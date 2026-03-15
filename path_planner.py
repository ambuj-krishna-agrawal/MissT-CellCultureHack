"""
Path planner for UR + RTDE that reduces singularity risk by:
1. Using a single fixed orientation (wrist 3 horizontal / parallel to ground) for all poses.
2. Moving via waypoints: lift to safe height → move XY → lower to target (no straight-line
   Cartesian move through singular configurations).

No guarantees: This does NOT guarantee singularity-free motion. The waypoints are chosen
heuristically; the arm can still hit elbow/shoulder/wrist singularities along a segment
or at a waypoint. For guaranteed avoidance you need either (a) joint-space planning with
checked joint limits and singular regions, or (b) a full motion planner (e.g. MoveIt)
with singularity-aware planning. Optional checks (is_near_singularity, check_after_move)
only detect when the current joint configuration is near known singular values; they
cannot predict singularities along the upcoming Cartesian path.
"""
from __future__ import annotations

import math
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


# Heuristic singular regions (joint angles in rad). UR: j0 base, j1 shoulder, j2 elbow, j3 wrist1, j4 wrist2, j5 wrist3.
# Wrist 2 (j4) near 0 or ±π: wrist axes align. Elbow (j2) near 0: arm extended; near ±π: folded.
WRIST2_SINGULAR_MARGIN = 0.15   # rad; avoid j4 in [-margin, +margin] or near ±π
ELBOW_EXTENDED_MARGIN = 0.2     # rad; avoid j2 near 0 (extended)
ELBOW_FOLDED_MARGIN = 0.25      # rad; avoid j2 near ±π (folded)


def is_near_singularity(q: Sequence[float]) -> tuple[bool, str]:
    """
    Check if joint angles q (rad, length 6) are near a known singular configuration.
    Returns (True, reason) if near singular, (False, "") otherwise. Heuristic only.
    """
    if len(q) < 6:
        return False, ""
    j2, j4 = float(q[2]), float(q[4])
    # Wrist 2 (j4) near 0 or ±π
    if abs(j4) < WRIST2_SINGULAR_MARGIN:
        return True, f"wrist2 (j4) near 0: j4={j4:.3f}"
    if abs(abs(j4) - math.pi) < WRIST2_SINGULAR_MARGIN:
        return True, f"wrist2 (j4) near ±π: j4={j4:.3f}"
    # Elbow (j2) extended or folded
    if abs(j2) < ELBOW_EXTENDED_MARGIN:
        return True, f"elbow (j2) extended: j2={j2:.3f}"
    if abs(abs(j2) - math.pi) < ELBOW_FOLDED_MARGIN:
        return True, f"elbow (j2) folded: j2={j2:.3f}"
    return False, ""


# Target joint values when nudging away from singular regions (rad). Stay outside margins.
NUDGE_WRIST2_SAFE = 0.25   # target |j4| when j4 was near 0
NUDGE_ELBOW_SAFE = 0.35    # target |j2| when j2 was near 0 (extended)
NUDGE_ELBOW_FOLDED_OFFSET = 0.2  # nudge j2 away from ±π by this amount


def nudge_away_from_singularity(q: Sequence[float]) -> List[float]:
    """
    Return a copy of q (length 6) with j2 and j4 adjusted so is_near_singularity returns False.
    Use when the target configuration would be singular; the resulting pose will be slightly
    different from the exact Cartesian target but the arm stays out of singularity.
    """
    if len(q) < 6:
        return list(q)[:6]
    out = [float(q[i]) for i in range(6)]
    j2, j4 = out[2], out[4]
    # Wrist 2 (j4): push out of [-margin, +margin] and away from ±π
    if abs(j4) < WRIST2_SINGULAR_MARGIN:
        out[4] = NUDGE_WRIST2_SAFE if j4 >= 0 else -NUDGE_WRIST2_SAFE
    elif abs(abs(j4) - math.pi) < WRIST2_SINGULAR_MARGIN:
        out[4] = (math.pi - NUDGE_WRIST2_SAFE) if j4 > 0 else (-math.pi + NUDGE_WRIST2_SAFE)
    # Elbow (j2): push out of extended (near 0) or folded (near ±π)
    if abs(j2) < ELBOW_EXTENDED_MARGIN:
        out[2] = NUDGE_ELBOW_SAFE if j2 >= 0 else -NUDGE_ELBOW_SAFE
    elif abs(abs(j2) - math.pi) < ELBOW_FOLDED_MARGIN:
        out[2] = (math.pi - NUDGE_ELBOW_FOLDED_OFFSET) if j2 > 0 else (-math.pi + NUDGE_ELBOW_FOLDED_OFFSET)
    return out


def moveL_path(
    rtde_c,
    waypoints: List[List[float]],
    speed: float,
    accel: float,
    rtde_r=None,
    check_singularity_after_move: bool = False,
) -> bool:
    """
    Execute a sequence of moveL commands. Returns True if all succeeded.
    If rtde_r is set and check_singularity_after_move is True, after each move we check
    current joint angles and return False (and stop) if near a singular configuration.
    """
    for pose in waypoints:
        ok = rtde_c.moveL(pose, speed, accel)
        if not ok:
            return False
        if check_singularity_after_move and rtde_r is not None:
            q = rtde_r.getActualQ()
            near, reason = is_near_singularity(q)
            if near:
                return False  # Caller can log reason; we don't have logging here
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
    check_singularity_after_move: bool = False,
) -> bool:
    """
    Move from current TCP pose to end_pose using a planned path (lift → move XY → lower)
    with fixed orientation (wrist 3 horizontal). Use this instead of a single moveL
    to reduce singularity risk. No guarantee: path can still pass through singularities.
    Set check_singularity_after_move=True to stop and return False if a waypoint
    ends in a near-singular joint configuration (requires rtde_r).
    """
    start_pose = list(rtde_r.getActualTCPPose())
    waypoints = plan_linear_path(
        start_pose,
        end_pose,
        fixed_orientation=fixed_orientation,
        safe_height=safe_height,
        min_lift_height=min_lift_height,
    )
    return moveL_path(
        rtde_c, waypoints, speed, accel,
        rtde_r=rtde_r if check_singularity_after_move else None,
        check_singularity_after_move=check_singularity_after_move,
    )


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
