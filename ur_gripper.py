import rtde_control

import time
import socket

from robotiq_gripper_control import RobotiqGripper
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface

ROBOT_IP = "192.168.12.52"  # change to your robotâ€™s IP
PORT = 63352            # Robotiq URCap port

NEUTRAL_POSE = [0.3, 0.6, 0.4, 3.18, 0.47, -0.148]
NEUTRAL_POSE2 = [0.3, 0.6, 0.5, 3.18, 0.47, -0.148]
DROP_OFF_POSE = [0.710, -0.3876, -.145, 0, 3.14, 0.0]
RETURN_POSE = [0.710, -0.3876, 0.08622, 0, 3.14, 0.0]

INS_INC_POSE = [-0.934, -0.567, 0.509, 0.066, 2.280, -2.180]
INS_INC_OUT = [-0.934, -0.381, 0.500, 0.068, 2.282, -2.173]

SPEED = 0.2        # m/s
ACCEL = 0.2        # m/s^2
FORCE = 20


def main():

    # Connect to robot
    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)
    gripper = RobotiqGripper(rtde_c)

    # Move to neutral/home

    print("Moving to neutral pose...")
    # gripper.activate()
    gripper.set_force(FORCE)
    # gripper.open()
    # # rtde_c.moveL(INS_INC_POSE, SPEED, ACCEL)
    # gripper.close()
    # rtde_c.moveL(INS_INC_OUT, SPEED, ACCEL)
    # gripper.close()

    rtde_c.moveL(INS_INC_POSE, SPEED, ACCEL)
    gripper.open()

    rtde_c.stopScript()
    rtde_c.disconnect()
    print("Control session ended.")


main()