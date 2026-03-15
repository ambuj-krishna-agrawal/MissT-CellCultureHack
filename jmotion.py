import rtde_control

from robotiq_gripper_control import RobotiqGripper
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface

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

# Waypoints for INC -> MICROSCOPE: lift, then move at safe height, then descend (avoids curved moveJ going out of bounds)
# Format: [x, y, z, rx, ry, rz]. Same orientation as INC/MICROSCOPE. Tune safe_z and mid point to your workspace.
INC_TO_MICROSCOPE_SAFE_Z = 0.55  # m, clear height above table/obstacles
INC_TO_MICROSCOPE_MID_XY = (-0.63, -0.438)  # (x, y) for mid waypoint above table
INC_TO_MICROSCOPE_WAYPOINTS = [
    [OUT_INC_POSE[0], OUT_INC_POSE[1], INC_TO_MICROSCOPE_SAFE_Z, 0.008, -2.123, 2.269],   # lift at incubator
    [INC_TO_MICROSCOPE_MID_XY[0], INC_TO_MICROSCOPE_MID_XY[1], INC_TO_MICROSCOPE_SAFE_Z, 0.008, -2.123, 2.269],
    list(TO_MICROSCOPE_POSE),                                                               # microscope (copy)
]
MICROSCOPE_TO_INC_WAYPOINTS = [
    [INC_TO_MICROSCOPE_MID_XY[0], INC_TO_MICROSCOPE_MID_XY[1], INC_TO_MICROSCOPE_SAFE_Z, 0.008, -2.123, 2.269],
    [OUT_INC_POSE[0], OUT_INC_POSE[1], INC_TO_MICROSCOPE_SAFE_Z, 0.008, -2.123, 2.269],
    list(OUT_INC_POSE),
]

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
    rtde_c.moveJ(TO_OPENER_POSE, SPEED, ACCEL)


def moveL_path(rtde_c, waypoints, speed=SPEED, accel=ACCEL):
    """
    Move through a sequence of Cartesian waypoints using linear (moveL) segments.
    This keeps the path piecewise linear and within the specified waypoints,
    avoiding the large curved motion that moveJ can produce in Cartesian space.
    waypoints: list of 6D poses [x, y, z, rx, ry, rz].
    """
    for pose in waypoints:
        rtde_c.moveL(pose, speed, accel)


def path_incubator_to_microscope(rtde_c, speed=SPEED, accel=ACCEL):
    """Move from outside incubator to microscope via safe waypoints (lift → over → descend)."""
    moveL_path(rtde_c, INC_TO_MICROSCOPE_WAYPOINTS, speed, accel)


def path_microscope_to_incubator(rtde_c, speed=SPEED, accel=ACCEL):
    """Move from microscope back to outside incubator via same safe corridor (reverse)."""
    moveL_path(rtde_c, MICROSCOPE_TO_INC_WAYPOINTS, speed, accel)


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
    """Single test motion: OUT_INC_POSE → microscope via control-point waypoints."""
    rtde_c, rtde_r, gripper = init_robot()
    rtde_c.moveL(OUT_INC_POSE, SPEED, ACCEL)  # start at outside incubator
    path_incubator_to_microscope(rtde_c)      # waypoint path to microscope
    rtde_c.stopScript()
    rtde_c.disconnect()


if __name__ == "__main__":
    run()


