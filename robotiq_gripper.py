"""
Robotiq gripper client (SDU Robotics style).
Based on https://sdurobotics.gitlab.io/ur_rtde/_static/robotiq_gripper.html
Communicates with the gripper via socket (port 63352) using SET/GET variable commands.
"""

from __future__ import annotations

import socket
import threading
import time
from collections import OrderedDict
from enum import Enum
from typing import Union


class RobotiqGripper:
    """Communicates with the gripper via socket with string commands (ACT, POS, SPE, FOR, etc.)."""

    ACT = "ACT"
    GTO = "GTO"
    ATR = "ATR"
    ADR = "ADR"
    FOR = "FOR"
    SPE = "SPE"
    POS = "POS"
    STA = "STA"
    PRE = "PRE"
    OBJ = "OBJ"
    FLT = "FLT"
    ENCODING = "UTF-8"

    class GripperStatus(Enum):
        RESET = 0
        ACTIVATING = 1
        ACTIVE = 3

    class ObjectStatus(Enum):
        MOVING = 0
        STOPPED_OUTER_OBJECT = 1
        STOPPED_INNER_OBJECT = 2
        AT_DEST = 3

    def __init__(self) -> None:
        self.socket: socket.socket | None = None
        self.command_lock = threading.Lock()
        self._min_position = 0
        self._max_position = 255
        self._min_speed = 0
        self._max_speed = 255
        self._min_force = 0
        self._max_force = 255

    def connect(self, hostname: str, port: int, socket_timeout: float = 2.0) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((hostname, port))
        self.socket.settimeout(socket_timeout)

    def disconnect(self) -> None:
        if self.socket:
            self.socket.close()
            self.socket = None

    def _set_vars(self, var_dict: OrderedDict[str, Union[int, float]]) -> bool:
        cmd = "SET"
        for variable, value in var_dict.items():
            cmd += f" {variable} {str(value)}"
        cmd += "\n"
        with self.command_lock:
            if self.socket is None:
                return False
            self.socket.sendall(cmd.encode(self.ENCODING))
            data = self.socket.recv(1024)
        return data == b"ack"

    def _set_var(self, variable: str, value: Union[int, float]) -> bool:
        return self._set_vars(OrderedDict([(variable, value)]))

    def _get_var(self, variable: str) -> int:
        with self.command_lock:
            if self.socket is None:
                raise RuntimeError("Gripper not connected")
            cmd = f"GET {variable}\n"
            self.socket.sendall(cmd.encode(self.ENCODING))
            data = self.socket.recv(1024)
        parts = data.decode(self.ENCODING).split()
        if len(parts) < 2 or parts[0] != variable:
            raise ValueError(f"Unexpected response: {data.decode(self.ENCODING)}")
        return int(parts[1])

    def _reset(self) -> None:
        self._set_var(self.ACT, 0)
        self._set_var(self.ATR, 0)
        while self._get_var(self.ACT) != 0 or self._get_var(self.STA) != 0:
            self._set_var(self.ACT, 0)
            self._set_var(self.ATR, 0)
            time.sleep(0.05)

    def activate(self, auto_calibrate: bool = False) -> None:
        """Activate the gripper (required after power-on or fault). Optionally auto-calibrate open/close range."""
        if not self.is_active():
            self._reset()
            while self._get_var(self.ACT) != 0 or self._get_var(self.STA) != 0:
                time.sleep(0.01)
        self._set_var(self.ACT, 1)
        time.sleep(1.0)
        while self._get_var(self.ACT) != 1 or self._get_var(self.STA) != 3:
            time.sleep(0.01)
        if auto_calibrate:
            self.auto_calibrate(log=False)

    def is_active(self) -> bool:
        status = self._get_var(self.STA)
        return self.GripperStatus(status) == self.GripperStatus.ACTIVE

    def get_open_position(self) -> int:
        return self._min_position

    def get_closed_position(self) -> int:
        return self._max_position

    def get_current_position(self) -> int:
        return self._get_var(self.POS)

    def get_status(self) -> int:
        return self._get_var(self.STA)

    def get_object_status(self) -> int:
        return self._get_var(self.OBJ)

    def move(self, position: int, speed: int = 128, force: int = 50) -> tuple[bool, int]:
        """Start moving to position (0=open, 255=closed). Returns (success, clipped_position)."""
        pos = max(self._min_position, min(position, self._max_position))
        spe = max(self._min_speed, min(speed, self._max_speed))
        force_val = max(self._min_force, min(force, self._max_force))
        var_dict = OrderedDict([(self.POS, pos), (self.SPE, spe), (self.FOR, force_val), (self.GTO, 1)])
        ok = self._set_vars(var_dict)
        return ok, pos

    def move_and_wait(
        self, position: int, speed: int = 128, force: int = 50, timeout: float = 10.0
    ) -> tuple[int, "RobotiqGripper.ObjectStatus"]:
        """Move to position and wait until motion completes or timeout. Returns (final_pos, object_status)."""
        ok, cmd_pos = self.move(position, speed, force)
        if not ok:
            raise RuntimeError("Failed to send move command")
        deadline = time.monotonic() + timeout
        while self._get_var(self.PRE) != cmd_pos and time.monotonic() < deadline:
            time.sleep(0.001)
        while time.monotonic() < deadline:
            cur_obj = self._get_var(self.OBJ)
            if self.ObjectStatus(cur_obj) != self.ObjectStatus.MOVING:
                final_pos = self._get_var(self.POS)
                return final_pos, self.ObjectStatus(cur_obj)
            time.sleep(0.01)
        final_pos = self._get_var(self.POS)
        return final_pos, self.ObjectStatus(self._get_var(self.OBJ))

    def open(self, speed: int = 128, force: int = 50, wait: bool = True) -> tuple[int, "RobotiqGripper.ObjectStatus"]:
        """Move to fully open. If wait, returns (position, object_status); else (0, AT_DEST)."""
        if wait:
            return self.move_and_wait(self._min_position, speed, force)
        self.move(self._min_position, speed, force)
        return 0, self.ObjectStatus.AT_DEST

    def close(self, speed: int = 128, force: int = 50, wait: bool = True) -> tuple[int, "RobotiqGripper.ObjectStatus"]:
        """Move to fully closed. If wait, returns (position, object_status); else (255, AT_DEST)."""
        if wait:
            return self.move_and_wait(self._max_position, speed, force)
        self.move(self._max_position, speed, force)
        return 255, self.ObjectStatus.AT_DEST

    def auto_calibrate(self, log: bool = True) -> None:
        """Calibrate min/max position by moving open and closed."""
        pos, status = self.move_and_wait(self._min_position, 64, 1)
        if status != self.ObjectStatus.AT_DEST:
            raise RuntimeError(f"Calibration open failed: {status}")
        pos, status = self.move_and_wait(self._max_position, 64, 1)
        if status != self.ObjectStatus.AT_DEST:
            raise RuntimeError(f"Calibration close failed: {status}")
        self._max_position = min(self._max_position, pos)
        pos, status = self.move_and_wait(self._min_position, 64, 1)
        if status != self.ObjectStatus.AT_DEST:
            raise RuntimeError(f"Calibration open back failed: {status}")
        self._min_position = max(self._min_position, pos)
        if log:
            print(f"Gripper calibrated to [{self._min_position}, {self._max_position}]")
