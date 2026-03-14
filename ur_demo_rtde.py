#!/usr/bin/env python3
"""
Combined demo using ur_rtde (SDU Robotics) for motion and the Robotiq gripper
socket (port 63352) for the gripper. One script: activate gripper, move left,
open, move right, close.

Install: pip install ur-rtde
Requires: Robotiq Gripper URCap on the robot (for port 63352).

Usage:
  python3 ur_demo_rtde.py ROBOT_IP
"""

from __future__ import annotations

import argparse
import socket
import sys
import time

GRIPPER_PORT = 63352
DEFAULT_LEFT = [0.35, 0.12, 0.35, 3.14159, 0.0, 0.0]
DEFAULT_RIGHT = [0.35, -0.12, 0.35, 3.14159, 0.0, 0.0]


def gripper_cmd(host: str, command: str, port: int = GRIPPER_PORT, timeout: float = 5.0) -> str:
    if not command.endswith("\n"):
        command = command + "\n"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.sendall(command.encode("utf-8"))
        try:
            return sock.recv(1024).decode("utf-8").strip()
        except socket.timeout:
            return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="ur_rtde motion + Robotiq gripper demo.")
    parser.add_argument("robot_ip", help="Robot IP address.")
    parser.add_argument("--velocity", type=float, default=0.1, help="moveL speed m/s.")
    parser.add_argument("--acceleration", type=float, default=1.0, help="moveL acceleration.")
    parser.add_argument("--external-control", action="store_true", help="Use External Control URCap.")
    args = parser.parse_args()

    try:
        import rtde_control
    except ImportError:
        print("Error: pip install ur-rtde", file=sys.stderr)
        return 1

    # Gripper: activate
    print("Activating gripper...")
    gripper_cmd(args.robot_ip, "SET ACT 1")
    time.sleep(1.5)

    if args.external_control:
        rtde_c = rtde_control.RTDEControlInterface(
            args.robot_ip, 500.0, rtde_control.RTDEControlInterface.FLAG_USE_EXT_UR_CAP
        )
    else:
        rtde_c = rtde_control.RTDEControlInterface(args.robot_ip, 500.0)

    try:
        if not rtde_c.isConnected():
            print("Error: Could not connect to robot.", file=sys.stderr)
            return 1
        print("Moving to left pose...")
        rtde_c.moveL(DEFAULT_LEFT, args.velocity, args.acceleration)
        print("Gripper open.")
        gripper_cmd(args.robot_ip, "SET POS 0")
        time.sleep(0.5)
        print("Moving to right pose...")
        rtde_c.moveL(DEFAULT_RIGHT, args.velocity, args.acceleration)
        print("Gripper close.")
        gripper_cmd(args.robot_ip, "SET POS 255")
        time.sleep(0.5)
        print("Done.")
        return 0
    finally:
        rtde_c.disconnect()


if __name__ == "__main__":
    sys.exit(main())
