#!/usr/bin/env python3
"""
Standalone script (no ROS, no Docker) to send URScript to a Universal Robot
so it moves the tool left and right in base frame.

Connects to the robot's Primary Interface (TCP port 30001), sends two movel
commands, then closes. Requires only Python 3 and the robot to be reachable
on the network. E-series robots must be in Remote Control mode for port 30001
to accept commands.

Usage:
  python3 ur_left_right.py ROBOT_IP
  python3 ur_left_right.py 192.168.56.101 --velocity 0.05
"""

from __future__ import annotations

import argparse
import socket
import sys

# Default poses in base frame [x, y, z, rx, ry, rz] (m, rad). Tool down.
DEFAULT_LEFT  = (0.35, 0.12, 0.35, 3.14159, 0.0, 0.0)
DEFAULT_RIGHT = (0.35, -0.12, 0.35, 3.14159, 0.0, 0.0)
PRIMARY_PORT = 30001


def build_script(
    left: tuple[float, ...],
    right: tuple[float, ...],
    acc: float = 1.0,
    vel: float = 0.1,
) -> str:
    """Build URScript: movel to left pose, then movel to right pose."""
    line = "movel(p[{:.5f}, {:.5f}, {:.5f}, {:.5f}, {:.5f}, {:.5f}], a={:.2f}, v={:.2f})\n"
    s = line.format(*left, acc, vel)
    s += line.format(*right, acc, vel)
    return s


def send_urscript(host: str, port: int, script: str, timeout: float = 5.0) -> None:
    """Send URScript to the robot over TCP. Each line must end with \\n."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.sendall(script.encode("utf-8"))


def parse_pose(s: str) -> tuple[float, ...]:
    """Parse 'x,y,z,rx,ry,rz' into a 6-tuple."""
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 6:
        raise ValueError("Pose must be 6 values: x,y,z,rx,ry,rz")
    return tuple(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send URScript to move the robot tool left and right (standalone, no ROS).",
    )
    parser.add_argument(
        "robot_ip",
        metavar="ROBOT_IP",
        help="Robot IP address (e.g. 192.168.56.101).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PRIMARY_PORT,
        help="Primary interface port (default: 30001).",
    )
    parser.add_argument(
        "--left-pose",
        type=str,
        default=None,
        metavar="x,y,z,rx,ry,rz",
        help="Left pose in base frame (m, rad).",
    )
    parser.add_argument(
        "--right-pose",
        type=str,
        default=None,
        metavar="x,y,z,rx,ry,rz",
        help="Right pose in base frame (m, rad).",
    )
    parser.add_argument(
        "--velocity",
        type=float,
        default=0.1,
        help="Tool speed for movel in m/s (default: 0.1).",
    )
    parser.add_argument(
        "--acceleration",
        type=float,
        default=1.0,
        help="Tool acceleration for movel (default: 1.0).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Socket timeout in seconds (default: 5.0).",
    )
    args = parser.parse_args()

    left = parse_pose(args.left_pose) if args.left_pose else DEFAULT_LEFT
    right = parse_pose(args.right_pose) if args.right_pose else DEFAULT_RIGHT

    script = build_script(left, right, acc=args.acceleration, vel=args.velocity)
    print(f"Sending URScript to {args.robot_ip}:{args.port}")
    print(script.strip())
    try:
        send_urscript(args.robot_ip, args.port, script, timeout=args.timeout)
        print("Done.")
        return 0
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
