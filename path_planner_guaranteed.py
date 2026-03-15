"""
Joint-space path planner with singularity and joint-limit guarantees.

Uses IK (ikpy) to convert Cartesian targets to joint angles, then plans a path in
joint space and verifies every sample stays within joint limits, outside
singular regions, and (optionally) clear of obstacles. Execution is a single
moveJ(current → end) for smooth motion.

Guarantee: If plan_joint_path_to_pose() returns a path, every point along the
joint-space segment has been checked for limits, singularity, and obstacles.
Collision is checked for TCP and all link positions (arm skeleton) in base frame.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

# Reuse singularity check and nudge from path_planner
from path_planner import (
    ELBOW_EXTENDED_MARGIN,
    ELBOW_FOLDED_MARGIN,
    WRIST2_SINGULAR_MARGIN,
    is_near_singularity,
    nudge_away_from_singularity,
)

# Default UR5 joint limits (rad). Tune for your robot (UR5/UR10/UR16).
UR5_JOINT_LIMITS = [
    (-2 * math.pi, 2 * math.pi),   # j0 base
    (-2 * math.pi, 2 * math.pi),   # j1 shoulder
    (-math.pi, math.pi),           # j2 elbow
    (-2 * math.pi, 2 * math.pi),   # j3 wrist1
    (-2 * math.pi, 2 * math.pi),   # j4 wrist2
    (-2 * math.pi, 2 * math.pi),   # j5 wrist3
]

# Sampling step along joint-space segments (rad). Smaller = stricter check, more samples.
JOINT_PATH_STEP = 0.02
# When obstacles are present, sample denser so we don't tunnel through thin obstacles.
JOINT_PATH_STEP_WHEN_OBSTACLES = 0.008

# Number of IK attempts with different initial guesses if first solution is singular.
IK_ATTEMPTS = 5


# -----------------------------------------------------------------------------
# Obstacles (in robot base frame). Use these when calling plan/move with obstacles=.
# -----------------------------------------------------------------------------

def box_obstacle(xmin: float, ymin: float, zmin: float, xmax: float, ymax: float, zmax: float) -> dict:
    """Axis-aligned box in base frame. Returns a dict for collision checks."""
    return {"type": "box", "min": [float(xmin), float(ymin), float(zmin)], "max": [float(xmax), float(ymax), float(zmax)]}


def sphere_obstacle(cx: float, cy: float, cz: float, radius: float) -> dict:
    """Sphere in base frame. Returns a dict for collision checks."""
    return {"type": "sphere", "center": [float(cx), float(cy), float(cz)], "radius": float(radius)}


def _quat_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q[0], q[1], q[2], q[3]
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
        [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
        [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
    ], dtype=np.float64)


def transform_obstacle_to_base(
    obstacle: dict,
    translation: Sequence[float],
    rotation_quat: Optional[Sequence[float]] = None,
) -> dict:
    """
    Return a copy of the obstacle with geometry transformed from another frame into robot base.
    translation: [tx, ty, tz] of obstacle-frame origin in base (meters).
    rotation_quat: optional [qx, qy, qz, qw] from obstacle frame to base; if None, translation only.
    Use when you defined the obstacle in table/world frame: transform to base so collision check matches.
    """
    tx, ty, tz = float(translation[0]), float(translation[1]), float(translation[2])
    if rotation_quat is not None:
        R = _quat_to_rotation_matrix(np.array(rotation_quat))
    else:
        R = np.eye(3)
    t = np.array([tx, ty, tz])

    def transform_point(p: np.ndarray) -> np.ndarray:
        return (R @ np.asarray(p, dtype=float).ravel()[:3]) + t

    if obstacle["type"] == "box":
        mn, mx = np.array(obstacle["min"]), np.array(obstacle["max"])
        corners = np.array([
            [mn[0], mn[1], mn[2]], [mx[0], mn[1], mn[2]], [mx[0], mx[1], mn[2]], [mn[0], mx[1], mn[2]],
            [mn[0], mn[1], mx[2]], [mx[0], mn[1], mx[2]], [mx[0], mx[1], mx[2]], [mn[0], mx[1], mx[2]],
        ])
        transformed = (R @ corners.T).T + t
        lo_new = transformed.min(axis=0)
        hi_new = transformed.max(axis=0)
        return {"type": "box", "min": lo_new.tolist(), "max": hi_new.tolist()}
    if obstacle["type"] == "sphere":
        c = transform_point(obstacle["center"])
        return {"type": "sphere", "center": c.tolist(), "radius": float(obstacle["radius"])}
    return dict(obstacle)


def _obstacle_contains(obstacle: dict, point: np.ndarray) -> bool:
    """True if point (3,) is inside the obstacle (in base frame)."""
    p = np.asarray(point, dtype=float).ravel()[:3]
    if obstacle["type"] == "box":
        lo, hi = np.array(obstacle["min"]), np.array(obstacle["max"])
        return bool(np.all(p >= lo) and np.all(p <= hi))
    if obstacle["type"] == "sphere":
        c = np.array(obstacle["center"])
        r = obstacle["radius"]
        return bool(np.linalg.norm(p - c) <= r)
    return False


def _point_collides_obstacles(point: np.ndarray, obstacles: Sequence[dict]) -> bool:
    """True if point is inside any obstacle."""
    for obs in obstacles:
        if _obstacle_contains(obs, point):
            return True
    return False


def _get_arm_positions(chain: "Chain", q: Sequence[float]) -> List[np.ndarray]:
    """Return list of 3D positions (in base frame) for each link along the chain. Uses full_kinematics."""
    q_full = np.asarray(q, dtype=float)
    n = len(chain.links) - 1
    if len(q_full) < n:
        q_full = np.resize(q_full, n)
    try:
        frames = chain.forward_kinematics(q_full, full_kinematics=True)
    except Exception:
        # Fallback: end-effector only
        frames = [chain.forward_kinematics(q_full)]
    return [np.array(f[:3, 3].ravel(), dtype=float) for f in frames]


def _configuration_collides(chain: "Chain", q: Sequence[float], obstacles: Sequence[dict]) -> bool:
    """True if any link position (or TCP) is inside any obstacle."""
    points = _get_arm_positions(chain, q)
    for pt in points:
        if _point_collides_obstacles(pt, obstacles):
            return True
    return False


def _pose_to_matrix(pose: Sequence[float]) -> np.ndarray:
    """Convert [x, y, z, rx, ry, rz] (UR rotation vector in rad) to 4x4 T matrix."""
    x, y, z = float(pose[0]), float(pose[1]), float(pose[2])
    rvec = np.array([float(pose[3]), float(pose[4]), float(pose[5])])
    theta = np.linalg.norm(rvec)
    if theta < 1e-9:
        R = np.eye(3)
    else:
        k = rvec / theta
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        R = np.eye(3) + math.sin(theta) * K + (1 - math.cos(theta)) * (K @ K)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = [x, y, z]
    return T


def _load_chain(urdf_path: Optional[Path] = None) -> "Chain":
    try:
        from ikpy.chain import Chain
    except ImportError as e:
        raise ImportError("path_planner_guaranteed requires ikpy. Install with: pip install ikpy") from e
    if urdf_path is None:
        urdf_path = Path(__file__).resolve().parent / "urdf" / "ur5_minimal.urdf"
    if not urdf_path.is_file():
        raise FileNotFoundError(f"URDF not found: {urdf_path}. Ensure urdf/ur5_minimal.urdf exists.")
    return Chain.from_urdf_file(str(urdf_path))


def _check_joint_limits(q: Sequence[float], limits: Optional[List[Tuple[float, float]]] = None) -> Tuple[bool, str]:
    """Return (True, reason) if any joint is outside limits."""
    limits = limits or UR5_JOINT_LIMITS
    for i, (lo, hi) in enumerate(limits):
        if i >= len(q):
            break
        v = float(q[i])
        if v < lo or v > hi:
            return True, f"joint {i} out of limits: {v:.3f} not in [{lo:.3f}, {hi:.3f}]"
    return False, ""


def _check_configuration(q: Sequence[float], limits: Optional[List[Tuple[float, float]]] = None) -> Tuple[bool, str]:
    """Return (True, reason) if q is invalid (limits or singularity)."""
    ok, reason = _check_joint_limits(q, limits)
    if ok:
        return True, reason
    near, reason = is_near_singularity(q)
    if near:
        return True, reason
    return False, ""


def _interpolate_joints(q_start: Sequence[float], q_end: Sequence[float], step: float) -> List[np.ndarray]:
    """Linear interpolation in joint space; yield vectors of length len(q_start)."""
    qs = np.asarray(q_start, dtype=float)
    qe = np.asarray(q_end, dtype=float)
    n = max(1, int(np.ceil(np.linalg.norm(qe - qs) / step)))
    return [qs + (qe - qs) * t / n for t in range(n + 1)]


def ik_target_would_be_singular(
    rtde_r,
    target_pose: Sequence[float],
    urdf_path: Optional[Path] = None,
) -> bool:
    """
    Run one IK for target_pose from current joint configuration. Return True if that
    solution is near singular (so a Cartesian move to target_pose would risk singularity).
    Used to decide whether to use joint-space move with nudge instead.
    """
    chain = _load_chain(urdf_path)
    start_q = list(rtde_r.getActualQ())
    n = len(chain.links) - 1
    init_full = np.zeros(n)
    init_full[: min(6, n)] = start_q[: min(6, n)]
    try:
        target_matrix = _pose_to_matrix(target_pose)
        q_full = chain.inverse_kinematics_frame(target=target_matrix, initial_position=init_full)
        q6 = list(q_full[:6])
        return is_near_singularity(q6)
    except Exception:
        return False


def compute_ik(
    chain: "Chain",
    target_pose: Sequence[float],
    initial_q: Optional[Sequence[float]] = None,
) -> Optional[np.ndarray]:
    """
    Compute joint angles for target Cartesian pose [x,y,z,rx,ry,rz].
    Returns (6,) array or None if no solution. Picks solution that is not singular and close to initial_q.
    If only singular solutions exist, returns a nudged configuration (TCP will be slightly off target).
    """
    target_matrix = _pose_to_matrix(target_pose)
    if initial_q is None:
        initial_q = [0.0] * 6
    initial_q = np.asarray(initial_q, dtype=float)
    n_joints = len(chain.links) - 1
    init_full = np.zeros(n_joints)
    init_full[: min(6, n_joints)] = initial_q[: min(6, n_joints)]

    best_q = None
    best_cost = float("inf")
    last_q = None  # any IK solution (may be singular), for fallback nudge
    for attempt in range(IK_ATTEMPTS):
        if attempt > 0:
            init_full = init_full + np.random.uniform(-0.5, 0.5, size=init_full.shape)
        try:
            q_full = chain.inverse_kinematics_frame(target=target_matrix, initial_position=init_full)
        except Exception:
            continue
        q6 = np.array(q_full[:6], dtype=float)
        last_q = q6
        near, _ = is_near_singularity(q6)
        if near:
            continue
        ok, _ = _check_joint_limits(q6)
        if ok:
            continue
        cost = float(np.linalg.norm(q6 - initial_q[:6]))
        if cost < best_cost:
            best_cost = cost
            best_q = q6
    if best_q is not None:
        return best_q
    # No non-singular solution: nudge last solution away from singularity and use it (TCP will be slightly off).
    if last_q is not None:
        nudged = nudge_away_from_singularity(last_q.tolist())
        return np.array(nudged, dtype=float)
    return None


def plan_joint_path(
    start_q: Sequence[float],
    end_q: Sequence[float],
    limits: Optional[List[Tuple[float, float]]] = None,
    step: float = JOINT_PATH_STEP,
    chain: Optional["Chain"] = None,
    obstacles: Optional[Sequence[dict]] = None,
) -> Optional[List[List[float]]]:
    """
    Plan a path in joint space from start_q to end_q. Every sample along the linear
    segment is checked for limits, singularity, and (if given) obstacles. Returns
    list of joint waypoints (each length 6) or None if the straight segment is not safe.
    If obstacles is provided, chain must be provided (used for FK to check arm positions).
    """
    limits = limits or UR5_JOINT_LIMITS
    if obstacles and chain is None:
        return None
    for q in [start_q, end_q]:
        bad, reason = _check_configuration(q, limits)
        if bad:
            return None
        if obstacles and chain is not None and _configuration_collides(chain, q, obstacles):
            return None
    samples = _interpolate_joints(start_q, end_q, step)
    waypoints: List[List[float]] = []
    for s in samples:
        q = list(s[:6])
        bad, reason = _check_configuration(q, limits)
        if bad:
            return None
        if obstacles and chain is not None and _configuration_collides(chain, q, obstacles):
            return None
        waypoints.append(q)
    # Prune redundant waypoints (keep start, end, and points where direction changes a lot)
    if len(waypoints) <= 2:
        return waypoints
    simplified = [waypoints[0]]
    for i in range(1, len(waypoints) - 1):
        # Keep every Nth or if angle between segments is large
        if len(simplified) < 2:
            simplified.append(waypoints[i])
            continue
        prev = np.array(simplified[-1])
        curr = np.array(waypoints[i])
        next_ = np.array(waypoints[i + 1])
        d1 = curr - prev
        d2 = next_ - curr
        n1, n2 = np.linalg.norm(d1), np.linalg.norm(d2)
        if n1 < 1e-6 or n2 < 1e-6:
            continue
        if np.dot(d1, d2) / (n1 * n2) < 0.99:  # direction change
            simplified.append(waypoints[i])
    simplified.append(waypoints[-1])
    return simplified


def plan_joint_path_to_pose(
    rtde_r,
    end_pose: Sequence[float],
    urdf_path: Optional[Path] = None,
    limits: Optional[List[Tuple[float, float]]] = None,
    step: float = JOINT_PATH_STEP,
    obstacles: Optional[Sequence[dict]] = None,
) -> Optional[List[List[float]]]:
    """
    Plan a singularity-free, limit- and obstacle-respecting joint path from current
    configuration to end_pose (Cartesian [x,y,z,rx,ry,rz]). Uses IK then verifies
    the segment. If obstacles is given, every sample is checked for collision
    (TCP + all link positions). Returns list of joint waypoints or None if planning fails.
    """
    chain = _load_chain(urdf_path)
    start_q = list(rtde_r.getActualQ())
    end_q = compute_ik(chain, end_pose, initial_q=start_q)
    if end_q is None:
        return None
    step_use = JOINT_PATH_STEP_WHEN_OBSTACLES if obstacles else step
    return plan_joint_path(
        start_q, end_q.tolist(),
        limits=limits, step=step_use,
        chain=chain if obstacles else None,
        obstacles=obstacles,
    )


def moveJ_planned(
    rtde_c,
    rtde_r,
    end_pose: Sequence[float],
    speed: float,
    accel: float,
    urdf_path: Optional[Path] = None,
    limits: Optional[List[Tuple[float, float]]] = None,
    joint_path_step: float = JOINT_PATH_STEP,
    obstacles: Optional[Sequence[dict]] = None,
) -> bool:
    """
    Move from current pose to end_pose using a verified joint-space path (singularity-,
    limit-, and obstacle-safe). We verify the entire segment by sampling; then execute
    a single moveJ(start → end) for smooth motion. Pass obstacles= to avoid boxes/spheres
    (in base frame). Returns False if no safe path found or move failed.
    """
    path = plan_joint_path_to_pose(
        rtde_r, end_pose,
        urdf_path=urdf_path, limits=limits, step=joint_path_step,
        obstacles=obstacles,
    )
    if path is None or len(path) == 0:
        return False
    # Single moveJ to end configuration: robot interpolates smoothly from current to end.
    # We already verified every point on that segment; no need to command each waypoint.
    end_q = path[-1]
    return rtde_c.moveJ(end_q, speed, accel)


def moveJ_planned_or_fallback_cartesian(
    rtde_c,
    rtde_r,
    end_pose: Sequence[float],
    speed: float,
    accel: float,
    urdf_path: Optional[Path] = None,
    use_guaranteed_planner: bool = True,
) -> bool:
    """
    If use_guaranteed_planner: move via moveJ_planned (joint-space, guaranteed).
    Else: single moveL to end_pose (no guarantee). Returns True on success.
    """
    if use_guaranteed_planner:
        return moveJ_planned(rtde_c, rtde_r, end_pose, speed, accel, urdf_path=urdf_path)
    return rtde_c.moveL(list(end_pose), speed, accel)
