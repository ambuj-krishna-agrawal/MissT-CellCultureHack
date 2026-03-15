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

INS_INC_POSE = [-0.934, -0.567, 0.509, 0.066, 2.280, -2.180]  # inside the incubator pose
OUT_INC_POSE = [-0.934, -0.381, 0.500, 0.068, 2.282, -2.173]  # outside the incubator pose
OPENER_POSE = [0.710, -0.3876, 0.08622, 0, 3.14, 0.0]  # opener pose -> random right now


SPEED = 0.2        # m/s
ACCEL = 0.2        # m/s^2
FORCE = 20

def init_robot():
    # Connect to robot
    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)
    gripper = RobotiqGripper(rtde_c)
    
    # activate gripper
    gripper.activate()
    gripper.set_force(FORCE)
    gripper.open()
    return rtde_c, rtde_r, gripper

def move_inside_incubator(rtde_c, gripper):
    rtde_c.moveL(INS_INC_POSE, SPEED, ACCEL)


def move_outside_incubator(rtde_c, gripper):
    rtde_c.moveL(OUT_INC_POSE, SPEED, ACCEL)

def move_towards_opener(rtde_c, gripper):
    rtde_c.moveJ(OPENER_POSE, SPEED, ACCEL)


def run():
    rtde_c, rtde_r, gripper = init_robot()   # step 1
    move_inside_incubator(rtde_c, gripper)   # step 2
    gripper.close()  # step 3: grip the object
    move_outside_incubator(rtde_c, gripper)   # step 3
    move_towards_opener(rtde_c, gripper)   # step 4
    gripper.close()   # step 5
    rtde_c.stopScript()
    rtde_c.disconnect()


if __name__ == "__main__":
    run()


