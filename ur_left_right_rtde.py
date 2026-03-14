#!/usr/bin/env python3
"""
Standalone script using ur_rtde (SDU Robotics) to move the robot arm.

Supports moveL (Cartesian), moveJ (joint space), and speedJ (joint velocity) so you
can use the same commands as in the ur_rtde examples. Install: pip install ur-rtde

By default: moveL left pose then right pose. Use --mode movej or --mode speedj to
use joint-space motion instead.

Usage:
  python3 ur_left_right_rtde.py ROBOT_IP
  python3 ur_left_right_rtde.py ROBOT_IP --mode movej --left-joints "0,-0.5,0.5,0,0.5,0" --right-joints "0,-0.5,0.5,0,-0.5,0"
  python3 ur_left_right_rtde.py ROBOT_IP --mode speedj --speedj-duration 2.0 --speedj "0.05,0,0,0,0,0"
"""

from __future__ import annotations

import argparse
import sys

# Default poses in base frame [x, y, z, rx, ry, rz] (m, rad). Tool down.
DEFAULT_LEFT = [0.35, 0.12, 0.35, 3.14159, 0.0, 0.0]
DEFAULT_RIGHT = [0.35, -0.12, 0.35, 3.14159, 0.0, 0.0]
# Default joint positions (rad) for moveJ: rough "left" and "right" for a 6-DOF UR.
DEFAULT_LEFT_JOINTS = [0.0, -0.8, 1.0, 0.0, 0.8, 0.0]
DEFAULT_RIGHT_JOINTS = [0.0, -0.8, 1.0, 0.0, 0.8, 3.14159]


def parse_pose(s: str) -> list[float]:
    """Parse 'x,y,z,rx,ry,rz' into a list of 6 floats."""
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 6:
        raise ValueError("Pose must be 6 values: x,y,z,rx,ry,rz")
    return parts


def parse_joints(s: str) -> list[float]:
    """Parse 'j1,j2,j3,j4,j5,j6' into a list of 6 joint angles (rad)."""
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 6:
        raise ValueError("Joints must be 6 values (rad): j1,j2,j3,j4,j5,j6")
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move robot using ur_rtde: moveL, moveJ, or speedJ.",
    )
    parser.add_argument("robot_ip", metavar="ROBOT_IP", help="Robot IP address.")
    parser.add_argument(
        "--mode",
        choices=["movel", "movej", "speedj"],
        default="movel",
        help="Motion type: movel (Cartesian), movej (joint target), speedj (joint velocity).",
    )
    # moveL options
    parser.add_argument("--left-pose", type=str, default=None, metavar="x,y,z,rx,ry,rz", help="Left pose for moveL (m, rad).")
    parser.add_argument("--right-pose", type=str, default=None, metavar="x,y,z,rx,ry,rz", help="Right pose for moveL (m, rad).")
    parser.add_argument("--velocity", type=float, default=0.1, help="moveL tool speed m/s or moveJ joint speed rad/s.")
    parser.add_argument("--acceleration", type=float, default=1.0, help="moveL/moveJ acceleration.")
    # moveJ options
    parser.add_argument("--left-joints", type=str, default=None, metavar="j1,...,j6", help="Left joint angles (rad) for moveJ.")
    parser.add_argument("--right-joints", type=str, default=None, metavar="j1,...,j6", help="Right joint angles (rad) for moveJ.")
    # speedJ options
    parser.add_argument(
        "--speedj",
        type=str,
        default=None,
        metavar="v1,v2,v3,v4,v5,v6",
        help="Joint velocities (rad/s) for speedJ. E.g. 0.05,0,0,0,0,0",
    )
    parser.add_argument("--speedj-duration", type=float, default=2.0, help="Seconds to run speedJ (default 2.0).")
    parser.add_argument("--speedj-acceleration", type=float, default=0.5, help="speedJ acceleration (rad/s^2).")
    #
    parser.add_argument("--external-control", action="store_true", help="Use External Control URCap.")
    parser.add_argument("--frequency", type=float, default=500.0, help="RTDE frequency Hz.")
    args = parser.parse_args()

    try:
        import rtde_control
    except ImportError:
        print("Error: ur_rtde not installed. Run: pip install ur-rtde", file=sys.stderr)
        return 1

    if args.external_control:
        rtde_c = rtde_control.RTDEControlInterface(
            args.robot_ip,
            args.frequency,
            rtde_control.RTDEControlInterface.FLAG_USE_EXT_UR_CAP,
        )
    else:
        rtde_c = rtde_control.RTDEControlInterface(args.robot_ip, args.frequency)

    try:
        if not rtde_c.isConnected():
            print("Error: Could not connect to robot.", file=sys.stderr)
            return 1

        if args.mode == "movel":
            left = parse_pose(args.left_pose) if args.left_pose else DEFAULT_LEFT.copy()
            right = parse_pose(args.right_pose) if args.right_pose else DEFAULT_RIGHT.copy()
            print("Connected. moveL to left pose, then right pose.")
            ok1 = rtde_c.moveL(left, args.velocity, args.acceleration)
            ok2 = rtde_c.moveL(right, args.velocity, args.acceleration) if ok1 else False
            print("Done." if (ok1 and ok2) else "One or more moveL failed.")
            return 0 if (ok1 and ok2) else 1

        if args.mode == "movej":
            left_j = parse_joints(args.left_joints) if args.left_joints else DEFAULT_LEFT_JOINTS.copy()
            right_j = parse_joints(args.right_joints) if args.right_joints else DEFAULT_RIGHT_JOINTS.copy()
            print("Connected. moveJ to left joints, then right joints.")
            ok1 = rtde_c.moveJ(left_j, args.velocity, args.acceleration)
            ok2 = rtde_c.moveJ(right_j, args.velocity, args.acceleration) if ok1 else False
            print("Done." if (ok1 and ok2) else "One or more moveJ failed.")
            return 0 if (ok1 and ok2) else 1

        if args.mode == "speedj":
            if not args.speedj:
                parser.error("--mode speedj requires --speedj v1,v2,v3,v4,v5,v6")
            joint_speed = parse_joints(args.speedj)
            dt = 1.0 / args.frequency
            duration = args.speedj_duration
            n_cycles = int(duration / dt)
            print(f"Connected. speedJ for {duration}s ({n_cycles} cycles).")
            for i in range(n_cycles):
                t_start = rtde_c.initPeriod()
                rtde_c.speedJ(joint_speed, args.speedj_acceleration, dt)
                rtde_c.waitPeriod(t_start)
            rtde_c.speedStop()
            print("Done.")
            return 0

        return 0
    finally:
        rtde_c.disconnect()


if __name__ == "__main__":
    sys.exit(main())
