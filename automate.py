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

def _move_to_pose(rtde_c, rtde_r, pose, obstacles=None):
    """Move to Cartesian pose; use guaranteed planner if enabled and available.
    If target pose would be singular, we use joint-space move to a nudged configuration (TCP slightly off).
    obstacles: optional list from path_planner_guaranteed (box_obstacle, sphere_obstacle).
    """
    def _cartesian_move():
        return moveL_planned_or_direct(
            rtde_c, rtde_r, pose, SPEED, ACCEL,
            fixed_orientation=WRIST3_HORIZONTAL_ORIENTATION,
            safe_height=SAFE_HEIGHT,
            use_planned_path=USE_PLANNED_PATH,
        )

    # When using Cartesian planner: if target would be singular, use joint move (nudged) instead
    if not USE_GUARANTEED_PLANNER:
        try:
            from path_planner_guaranteed import moveJ_planned, ik_target_would_be_singular
            if ik_target_would_be_singular(rtde_r, pose):
                return moveJ_planned(rtde_c, rtde_r, pose, SPEED, ACCEL, obstacles=obstacles or OBSTACLES)
        except Exception:
            pass
        return _cartesian_move()
    try:
        from path_planner_guaranteed import moveJ_planned
        return moveJ_planned(rtde_c, rtde_r, pose, SPEED, ACCEL, obstacles=obstacles or OBSTACLES)
    except ImportError:
        return _cartesian_move()

ROBOT_IP = "192.168.12.52"  # change to your robotâ€™s IP
PORT = 63352            # Robotiq URCap port

NEUTRAL_POSE = [0.3, 0.6, 0.4, 3.18, 0.47, -0.148]
NEUTRAL_POSE2 = [0.3, 0.6, 0.5, 3.18, 0.47, -0.148]
DROP_OFF_POSE = [0.710, -0.3876, -.145, 0, 3.14, 0.0]
RETURN_POSE = [0.710, -0.3876, 0.08622, 0, 3.14, 0.0]

# Inside incubator: far reach (x=-1.044) can force elbow extended or wrist singular. If you hit singularity:
# - Set USE_GUARANTEED_PLANNER = True (joint-space path avoids singular corridor), or
# - Raise SAFE_HEIGHT so the "above" waypoint is higher, or
# - Slightly change orientation (rx,ry,rz) so the same (x,y,z) is reached with different joints.
INS_INC_POSE = [-1.044, -0.578, 0.461, 0.008, -2.123, 2.269]  # inside the incubator pose
OUT_INC_POSE = [-1.044, -0.298, 0.461, 0.008, -2.123, 2.269]  # outside the incubator pose
TO_MICROSCOPE_POSE = [-0.215, -0.578, 0.277, 0.008, -2.123, 2.269]  # go to the microscope pose
AWAY_MICROSCOPE_POSE = [-0.215, -0.298, 0.477, 0.008, -2.123, 2.269] 
TO_OPENER_POSE = [-0.530, -0.0367, 0.165, 0.008, -2.123, 2.269]  # opener pose -> random right now

TO_FRIDGE_POSE = [-0.706, -0.221, -0.338, 0.008, -2.123, 2.269]  # fridge pose -> random right now
TO_FRIDGE_DOOR_POSE = [-0.706, -0.328, -0.338, 0.008, -2.123, 2.269]  # fridge pose -> random right now
OPEN_FRIDGE_DOOR_POSE = [-0.924, -0.328, -0.338, 0.008, -2.123, 2.269]  # open the fridge pose -> random right now
BACK_FROM_FRIDGE_DOOR_POSE = [-0.925, -0.243, -0.338, 0.008, -2.123, 2.269]  # back from the fridge pose -> random right now

TO_AWAY_FROM_REAGENT_POSE = [-0.774, -0.074, -0.131, 0.008, -2.123, 2.169]  # away from the reagent pose -> random right now
TO_REAGENT_POSE = [-0.774, -0.444, -0.131, 0.008, -2.123, 2.269]  # to the reagent pose -> random right now


SPEED = 0.2        # m/s
ACCEL = 0.2        # m/s^2
FORCE = 20

# Path planner: safe height for lift→move→lower (avoids singularities); fixed orientation = wrist 3 horizontal
SAFE_HEIGHT = 0.55  # m; raise if move_inside_incubator hits singularity (waypoints stay higher longer)
USE_PLANNED_PATH = False  # use waypoints (lift → move XY → lower) instead of direct moveL
# Guaranteed planner: joint-space path with singularity/limit checks (requires ikpy + urdf/ur5_minimal.urdf)
USE_GUARANTEED_PLANNER = True  # set True for joint-space guaranteed avoidance; falls back to Cartesian if ikpy missing
# Obstacles must be in robot base frame (same as URDF base_link: origin at robot base, axes match robot).
# If the robot still goes through the obstacle, your coords may be in another frame (table/world).
# Then use transform_obstacle_to_base(obs, translation=[tx,ty,tz], rotation_quat=None) and pass the result.
try:
    from path_planner_guaranteed import box_obstacle, sphere_obstacle, transform_obstacle_to_base
    OBSTACLES = [
        box_obstacle(-1.2, -0.34, -0.09, 1.2, -0.32, 0.09),
        # If obstacle was defined in table frame: transform_obstacle_to_base(box_obstacle(...), [table_x, table_y, table_z]),
    ]
except ImportError:
    OBSTACLES = []

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

def check_incubator_pose_singularity(rtde_r):
    """Call once (e.g. after init_robot) to print joint angles for INS_INC_POSE and if they're near singular."""
    try:
        from path_planner_guaranteed import _load_chain, compute_ik
        from path_planner import is_near_singularity
        chain = _load_chain()
        start_q = list(rtde_r.getActualQ())
        end_q = compute_ik(chain, INS_INC_POSE, initial_q=start_q)
        if end_q is None:
            print("INS_INC_POSE: IK failed (no solution or all solutions singular).")
            return
        near, reason = is_near_singularity(end_q.tolist())
        print("INS_INC_POSE joint angles (rad):", [round(x, 3) for x in end_q])
        print("  j2 (elbow):", round(end_q[2], 3), "  j4 (wrist2):", round(end_q[4], 3))
        print("  Near singularity:", near, reason if near else "")
    except Exception as e:
        print("check_incubator_pose_singularity:", e)


def move_inside_incubator(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, INS_INC_POSE)


def move_outside_incubator(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, OUT_INC_POSE)


def move_towards_opener(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, TO_OPENER_POSE)


def move_to_microscope(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, TO_MICROSCOPE_POSE)

def move_away_from_microscope(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, AWAY_MICROSCOPE_POSE)

def move_to_fridge(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, TO_FRIDGE_POSE)

def move_to_fridge_door(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, TO_FRIDGE_DOOR_POSE)

def open_fridge_door(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, OPEN_FRIDGE_DOOR_POSE)

def back_from_fridge_door(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, BACK_FROM_FRIDGE_DOOR_POSE)

def move_to_away_from_reagent(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, TO_AWAY_FROM_REAGENT_POSE)


def move_to_reagent(rtde_c, rtde_r, gripper):
    _move_to_pose(rtde_c, rtde_r, TO_REAGENT_POSE)



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
    # move_outside_incubator(rtde_c, rtde_r, gripper)  # step 1
    # move_inside_incubator(rtde_c, rtde_r, gripper)
    # move_outside_incubator(rtde_c, rtde_r, gripper) 
    # move_to_microscope(rtde_c, rtde_r, gripper)
    # move_outside_incubator(rtde_c, rtde_r, gripper)
    # # move_away_from_microscope(rtde_c, rtde_r, gripper)
    # move_to_fridge(rtde_c, rtde_r, gripper)
    # move_to_fridge_door(rtde_c, rtde_r, gripper)
    # open_fridge_door(rtde_c, rtde_r, gripper)
    # back_from_fridge_door(rtde_c, rtde_r, gripper)
    # # gripper.close()  # step 3: grip the object
    # # move_outside_incubator(rtde_c, rtde_r, gripper)
    # move_to_away_from_reagent(rtde_c, rtde_r, gripper)
    # move_to_reagent(rtde_c, rtde_r, gripper)
    # gripper.close()
    move_to_away_from_reagent(rtde_c, rtde_r, gripper)
    move_outside_incubator(rtde_c, rtde_r, gripper)
    move_to_microscope(rtde_c, rtde_r, gripper)
    # gripper.open()
    


if __name__ == "__main__":
    run()


