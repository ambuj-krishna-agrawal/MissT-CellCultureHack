#!/usr/bin/env python3
"""
Standalone script (no ROS, no Docker) to control a Robotiq 2F-85 gripper
mounted on a Universal Robot.

The Robotiq Gripper URCap runs a socket server on the robot at port 63352.
Connect to ROBOT_IP:63352 and send ASCII commands (each ending with \\n).
Requires the Robotiq Gripper URCap to be installed on the robot.

Usage:
  python3 ur_gripper.py ROBOT_IP activate
  python3 ur_gripper.py 192.168.56.101 open
  python3 ur_gripper.py 192.168.56.101 close
  python3 ur_gripper.py 192.168.56.101 pos 128
  python3 ur_gripper.py 192.168.56.101 get-pos
"""

from __future__ import annotations

import argparse
import socket
import sys

GRIPPER_PORT = 63352
DEFAULT_TIMEOUT = 5.0


def send_command(host: str, port: int, command: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Send one line to the gripper server; return the reply (if any)."""
    if not command.endswith("\n"):
        command = command + "\n"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.sendall(command.encode("utf-8"))
        try:
            reply = sock.recv(1024).decode("utf-8").strip()
            return reply
        except socket.timeout:
            return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Control Robotiq 2F-85 gripper via socket (robot IP, port 63352).",
    )
    parser.add_argument(
        "robot_ip",
        metavar="ROBOT_IP",
        help="Robot IP address (gripper URCap listens on this host, port 63352).",
    )
    parser.add_argument(
        "action",
        choices=["activate", "open", "close", "pos", "get-pos", "get-sta", "get-obj"],
        help="activate | open | close | pos N | get-pos | get-sta | get-obj",
    )
    parser.add_argument(
        "value",
        nargs="?",
        default=None,
        help="For 'pos': position 0 (open) to 255 (closed).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=GRIPPER_PORT,
        help="Gripper socket port (default: 63352).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Socket timeout in seconds.",
    )
    args = parser.parse_args()

    if args.action == "pos" and args.value is None:
        parser.error("action 'pos' requires a value 0–255")
    if args.action == "pos":
        try:
            pos = int(args.value)
            if not 0 <= pos <= 255:
                raise ValueError("out of range")
        except ValueError:
            parser.error("position must be an integer 0–255")
        command = f"SET POS {pos}"
    elif args.action == "activate":
        command = "SET ACT 1"
    elif args.action == "open":
        command = "SET POS 0"
    elif args.action == "close":
        command = "SET POS 255"
    elif args.action == "get-pos":
        command = "GET POS"
    elif args.action == "get-sta":
        command = "GET STA"
    elif args.action == "get-obj":
        command = "GET OBJ"
    else:
        command = ""

    try:
        reply = send_command(args.robot_ip, args.port, command, timeout=args.timeout)
        if reply:
            print(reply)
        elif args.action in ("activate", "open", "close", "pos"):
            print("OK")
        return 0
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
