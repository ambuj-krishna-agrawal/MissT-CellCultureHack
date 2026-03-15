import rtde_control
import time
from time import sleep

from robotiq_gripper_control import RobotiqGripper
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from path_planner import (
    WRIST3_HORIZONTAL_ORIENTATION,
    moveL_planned_or_direct,
    apply_fixed_orientation,
)

ROBOT_IP = "192.168.12.52"  # change to your robotâ€™s IP
PORT = 63352            # Robotiq URCap port

NEUTRAL_POSE = [0.3, 0.6, 0.4, 3.18, 0.47, -0.148]
NEUTRAL_POSE2 = [0.3, 0.6, 0.5, 3.18, 0.47, -0.148]
DROP_OFF_POSE = [0.710, -0.3876, -.145, 0, 3.14, 0.0]
RETURN_POSE = [0.710, -0.3876, 0.08622, 0, 3.14, 0.0]

INS_INC_POSE = [-1.044, -0.578, 0.461, 0.008, -2.123, 2.269]  # inside the incubator pose
OUT_INC_POSE = [-1.044, -0.298, 0.461, 0.008, -2.123, 2.269]  # outside the incubator pose
TO_MICROSCOPE_POSE = [-0.215, -0.578, 0.277, 0.008, -2.123, 2.269]  # go to the microscope pose
TO_OPENER_POSE = [-0.530, -0.0367, 0.165, 0.008, -2.123, 2.269]  # opener pose -> random right now

TO_FRIDGE_POSE = [-0.706, -0.221, -0.338, 0.008, -2.123, 2.269]  # fridge pose -> random right now
TO_FRIDGE_DOOR_POSE = [-0.706, -0.328, -0.338, 0.008, -2.123, 2.269]  # fridge pose -> random right now
OPEN_FRIDGE_DOOR_POSE = [-0.924, -0.328, -0.338, 0.008, -2.123, 2.269]  # open the fridge pose -> random right now
BACK_FROM_FRIDGE_DOOR_POSE = [-0.925, -0.243, -0.338, 0.008, -2.123, 2.269]  # back from the fridge pose -> random right now

TO_AWAY_FROM_REAGENT_POSE = [-0.774, -0.274, -0.131, 0.008, -2.123, 2.269]  # away from the reagent pose -> random right now
TO_REAGENT_POSE = [-0.774, -0.444, -0.131, 0.008, -2.123, 2.269]  # to the reagent pose -> random right now


SPEED = 0.2        # m/s
ACCEL = 0.2        # m/s^2
FORCE = 20

# Path planner: safe height for lift→move→lower (avoids singularities); fixed orientation = wrist 3 horizontal
SAFE_HEIGHT = 0.5  # m; tune to clear obstacles
USE_PLANNED_PATH = True  # use waypoints (lift → move XY → lower) instead of direct moveL

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

def move_inside_incubator(rtde_c, rtde_r, gripper):
    moveL_planned_or_direct(
        rtde_c, rtde_r, INS_INC_POSE, SPEED, ACCEL,
        fixed_orientation=WRIST3_HORIZONTAL_ORIENTATION,
        safe_height=SAFE_HEIGHT,
        use_planned_path=USE_PLANNED_PATH,
    )


def move_outside_incubator(rtde_c, rtde_r, gripper):
    moveL_planned_or_direct(
        rtde_c, rtde_r, OUT_INC_POSE, SPEED, ACCEL,
        fixed_orientation=WRIST3_HORIZONTAL_ORIENTATION,
        safe_height=SAFE_HEIGHT,
        use_planned_path=USE_PLANNED_PATH,
    )


def move_towards_opener(rtde_c, rtde_r, gripper):
    moveL_planned_or_direct(
        rtde_c, rtde_r, TO_OPENER_POSE, SPEED, ACCEL,
        fixed_orientation=WRIST3_HORIZONTAL_ORIENTATION,
        safe_height=SAFE_HEIGHT,
        use_planned_path=USE_PLANNED_PATH,
    )


def shake(rtde_c, rtde_r, n_shakes=4, tilt_angle=0.15, speed=0.15):
    """Rotate the gripper along the y-axis, tilting left and right a few times."""
    pose = list(rtde_r.getActualTCPPose())
    # pose = [x, y, z, rx, ry, rz]; ry is rotation around y-axis
    left = pose.copy()
    right = pose.copy()
    left[4] += tilt_angle   # tilt one way
    right[4] -= tilt_angle  # tilt the other way
    for _ in range(n_shakes):
        rtde_c.moveL(left, speed, ACCEL)
        rtde_c.moveL(right, speed, ACCEL)
    # return to original pose
    rtde_c.moveL(pose, speed, ACCEL)


def run():
    # rtde_c, rtde_r, gripper = init_robot()   # step 1
    # move_inside_incubator(rtde_c, gripper)   # step 2
    # gripper.close()  # step 3: grip the object
    # move_outside_incubator(rtde_c, gripper)   # step 3
    # shake(rtde_c, rtde_r)   # step 4: shake the object
    # move_towards_opener(rtde_c, gripper)   # step 4
    # gripper.close()   # step 5
    # rtde_c.stopScript()
    # rtde_c.disconnect()



    # workflow 1
    rtde_c, rtde_r, gripper = init_robot()   # step 1
    ## rtde_c.moveJ(OUT_INC_POSE, SPEED, ACCEL)  # assume the robot is at the outside of the incubator
    # rtde_c.moveL(INS_INC_POSE, SPEED, ACCEL)
    # gripper.close()  # step 3: grip the object
    # rtde_c.moveL(OUT_INC_POSE, SPEED, ACCEL)
    # rtde_c.moveJ(TO_MICROSCOPE_POSE, SPEED, ACCEL)
    # gripper.open()
    # sleep(10)
    # gripper.close()
    # rtde_c.moveJ(OUT_INC_POSE, SPEED, ACCEL)
    # rtde_c.moveL(INS_INC_POSE, SPEED, ACCEL)
    # gripper.open()
    # rtde_c.moveL(OUT_INC_POSE, SPEED, ACCEL)
    # gripper.close()   # step 5
    # rtde_c.stopScript()
    # rtde_c.disconnect()

    move_inside_incubator(rtde_c, rtde_r, gripper)
    gripper.close()  # step 3: grip the object
    move_outside_incubator(rtde_c, rtde_r, gripper)


if __name__ == "__main__":
    run()


