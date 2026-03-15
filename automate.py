import logging
import sys
import traceback

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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
LOG = logging.getLogger("automate")

def _move_to_pose(rtde_c, rtde_r, pose, obstacles=None):
    """Move to Cartesian pose; use guaranteed planner if enabled and available."""
    current_q = list(rtde_r.getActualQ())
    current_tcp = list(rtde_r.getActualTCPPose())
    LOG.debug("_move_to_pose → target=%s, planner=%s",
              [round(v, 4) for v in pose],
              "guaranteed" if USE_GUARANTEED_PLANNER else "cartesian")
    LOG.debug("  current joints: %s", [round(v, 3) for v in current_q])
    LOG.debug("  current TCP:    %s", [round(v, 4) for v in current_tcp])

    def _cartesian_move():
        LOG.debug("Using Cartesian moveL (safe_height=%.2f, planned=%s)", SAFE_HEIGHT, USE_PLANNED_PATH)
        try:
            result = moveL_planned_or_direct(
                rtde_c, rtde_r, pose, SPEED, ACCEL,
                fixed_orientation=WRIST3_HORIZONTAL_ORIENTATION,
                safe_height=SAFE_HEIGHT,
                use_planned_path=USE_PLANNED_PATH,
            )
            if not result:
                LOG.error("Cartesian moveL returned False — robot did NOT move!")
            else:
                LOG.debug("Cartesian move completed successfully")
            return result
        except Exception as e:
            LOG.error("Cartesian move FAILED: %s\n%s", e, traceback.format_exc())
            raise

    if not USE_GUARANTEED_PLANNER:
        try:
            from path_planner_guaranteed import moveJ_planned, ik_target_would_be_singular
            if ik_target_would_be_singular(rtde_r, pose):
                LOG.info("Target would be singular — using joint-space moveJ instead")
                result = moveJ_planned(rtde_c, rtde_r, pose, SPEED, ACCEL, obstacles=obstacles or OBSTACLES)
                if not result:
                    LOG.error("Singular-fallback moveJ returned False — robot did NOT move!")
                return result
        except Exception as e:
            LOG.warning("Singularity check failed (%s), falling back to Cartesian", e)
        return _cartesian_move()

    try:
        from path_planner_guaranteed import (
            moveJ_planned, plan_joint_path_to_pose, compute_ik, _load_chain,
        )
        from path_planner import is_near_singularity
        LOG.debug("Using guaranteed joint-space moveJ")

        chain = _load_chain()
        end_q = compute_ik(chain, pose, initial_q=current_q)
        if end_q is None:
            LOG.error("IK FAILED for target %s — no joint solution found!", [round(v, 4) for v in pose])
            LOG.error("  Falling back to Cartesian moveL")
            return _cartesian_move()

        LOG.debug("  IK solution: %s", [round(v, 3) for v in end_q])
        near, reason = is_near_singularity(end_q.tolist())
        if near:
            LOG.warning("  IK solution is near singularity: %s", reason)

        path = plan_joint_path_to_pose(rtde_r, pose, obstacles=obstacles or OBSTACLES)
        if path is None:
            LOG.error("Path planning FAILED (singularity/limits/collision along segment)")
            LOG.error("  start_q=%s", [round(v, 3) for v in current_q])
            LOG.error("  end_q=  %s", [round(v, 3) for v in end_q])
            LOG.error("  Falling back to Cartesian moveL")
            return _cartesian_move()

        LOG.debug("  Path planned OK: %d waypoints", len(path))
        result = rtde_c.moveJ(path[-1], SPEED, ACCEL)
        if not result:
            LOG.error("moveJ returned False — robot did NOT execute the move!")
        else:
            LOG.debug("Guaranteed moveJ completed successfully")
        return result

    except ImportError:
        LOG.warning("path_planner_guaranteed not available, falling back to Cartesian")
        return _cartesian_move()
    except Exception as e:
        LOG.error("Guaranteed moveJ FAILED: %s\n%s", e, traceback.format_exc())
        raise

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
TO_REAGENT_POSE = [-0.764, -0.453, -0.142, 0.008, -2.123, 2.269]  # to the reagent pose -> random right now

TO_DECAP_POSE = [-0.530, -0.437, 0.165, 0.008, -2.123, 2.269]  # to the decapotentable pose -> random right now
TO_DECAP_POSE_UP = [-0.530, -0.437, 0.277, 0.008, -2.123, 2.269]  # to the decapotentable pose -> random right now
TO_DECAP_AWAY_POSE = [-0.530, -0.237, 0.165, 0.008, -2.123, 2.269]  # to the decap away pose -> random right now

TO_REAGENT_TABLE_POSE = [-0.707, -0.443, 0.181, 0.008, -2.123, 2.269]  # to the reagent table pose -> random right now
TO_REAGENT_TABLE_AWAY_POSE = [-0.707, -0.243, 0.181, 0.008, -2.123, 2.269]  # to the reagent table away pose -> random right now

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
        # box_obstacle(-1.2, -0.34, -0.09, 1.2, -0.32, 0.09),
        # If obstacle was defined in table frame: transform_obstacle_to_base(box_obstacle(...), [table_x, table_y, table_z]),
    ]
except ImportError:
    OBSTACLES = []

def init_robot():
    LOG.info("Connecting to robot at %s ...", ROBOT_IP)
    try:
        rtde_c = RTDEControlInterface(ROBOT_IP)
        LOG.info("RTDE Control interface connected")
    except Exception as e:
        LOG.error("RTDE Control connection FAILED: %s\n%s", e, traceback.format_exc())
        raise

    try:
        rtde_r = RTDEReceiveInterface(ROBOT_IP)
        LOG.info("RTDE Receive interface connected")
    except Exception as e:
        LOG.error("RTDE Receive connection FAILED: %s\n%s", e, traceback.format_exc())
        raise

    try:
        gripper = RobotiqGripper(rtde_c)
        gripper.set_force(FORCE)
        gripper.open()
        LOG.info("Gripper initialized (force=%d, opened)", FORCE)
    except Exception as e:
        LOG.error("Gripper init FAILED: %s\n%s", e, traceback.format_exc())
        raise

    LOG.info("Robot fully initialized")
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


def _logged_move(name, rtde_c, rtde_r, pose):
    LOG.info("▶ %s", name)
    t0 = time.time()
    try:
        _move_to_pose(rtde_c, rtde_r, pose)
        LOG.info("✓ %s completed (%.1fs)", name, time.time() - t0)
    except Exception as e:
        LOG.error("✗ %s FAILED after %.1fs: %s", name, time.time() - t0, e)
        raise


def _logged_gripper(action, gripper):
    LOG.info("▶ gripper.%s()", action)
    t0 = time.time()
    try:
        getattr(gripper, action)()
        LOG.info("✓ gripper.%s() completed (%.1fs)", action, time.time() - t0)
    except Exception as e:
        LOG.error("✗ gripper.%s() FAILED after %.1fs: %s", action, time.time() - t0, e)
        raise


def move_inside_incubator(rtde_c, rtde_r, gripper):
    _logged_move("move_inside_incubator", rtde_c, rtde_r, INS_INC_POSE)


def move_outside_incubator(rtde_c, rtde_r, gripper):
    _logged_move("move_outside_incubator", rtde_c, rtde_r, OUT_INC_POSE)


def move_towards_opener(rtde_c, rtde_r, gripper):
    _logged_move("move_towards_opener", rtde_c, rtde_r, TO_OPENER_POSE)


def move_to_microscope(rtde_c, rtde_r, gripper):
    _logged_move("move_to_microscope", rtde_c, rtde_r, TO_MICROSCOPE_POSE)

def move_away_from_microscope(rtde_c, rtde_r, gripper):
    _logged_move("move_away_from_microscope", rtde_c, rtde_r, AWAY_MICROSCOPE_POSE)

def move_to_fridge(rtde_c, rtde_r, gripper):
    _logged_move("move_to_fridge", rtde_c, rtde_r, TO_FRIDGE_POSE)

def move_to_fridge_door(rtde_c, rtde_r, gripper):
    _logged_move("move_to_fridge_door", rtde_c, rtde_r, TO_FRIDGE_DOOR_POSE)

def open_fridge_door(rtde_c, rtde_r, gripper):
    _logged_move("open_fridge_door", rtde_c, rtde_r, OPEN_FRIDGE_DOOR_POSE)

def back_from_fridge_door(rtde_c, rtde_r, gripper):
    _logged_move("back_from_fridge_door", rtde_c, rtde_r, BACK_FROM_FRIDGE_DOOR_POSE)

def move_to_away_from_reagent(rtde_c, rtde_r, gripper):
    _logged_move("move_to_away_from_reagent", rtde_c, rtde_r, TO_AWAY_FROM_REAGENT_POSE)


def move_to_reagent(rtde_c, rtde_r, gripper):
    _logged_move("move_to_reagent", rtde_c, rtde_r, TO_REAGENT_POSE)


def move_to_decap_table(rtde_c, rtde_r, gripper):
    _logged_move("move_to_decap_table", rtde_c, rtde_r, TO_DECAP_POSE)

def move_to_decap_away(rtde_c, rtde_r, gripper):
    _logged_move("move_to_decap_away", rtde_c, rtde_r, TO_DECAP_AWAY_POSE)

def move_to_decap_pose_up(rtde_c, rtde_r, gripper):
    _logged_move("move_to_decap_pose_up", rtde_c, rtde_r, TO_DECAP_POSE_UP)

def move_to_reagent_table(rtde_c, rtde_r, gripper):
    _logged_move("move_to_reagent_table", rtde_c, rtde_r, TO_REAGENT_TABLE_POSE)

def move_to_reagent_table_away(rtde_c, rtde_r, gripper):
    _logged_move("move_to_reagent_table_away", rtde_c, rtde_r, TO_REAGENT_TABLE_AWAY_POSE)

def shake(rtde_c, rtde_r, n_shakes=4, tilt_angle=0.15, speed=0.15):
    """Rotate the gripper along the y-axis, tilting left and right a few times."""
    LOG.info("▶ shake (n=%d, tilt=%.3f, speed=%.3f)", n_shakes, tilt_angle, speed)
    t0 = time.time()
    try:
        pose = list(rtde_r.getActualTCPPose())
        LOG.debug("Current TCP pose: %s", [round(v, 4) for v in pose])
        left = pose.copy()
        right = pose.copy()
        left[4] += tilt_angle
        right[4] -= tilt_angle
        for i in range(n_shakes):
            LOG.debug("Shake %d/%d", i + 1, n_shakes)
            rtde_c.moveL(left, speed, ACCEL)
            rtde_c.moveL(right, speed, ACCEL)
        rtde_c.moveL(pose, speed, ACCEL)
        LOG.info("✓ shake completed (%.1fs)", time.time() - t0)
    except Exception as e:
        LOG.error("✗ shake FAILED after %.1fs: %s\n%s", time.time() - t0, e, traceback.format_exc())
        raise


def protocol_1_step_1(rtde_c, rtde_r, gripper):
    move_outside_incubator(rtde_c, rtde_r, gripper)
    move_inside_incubator(rtde_c, rtde_r, gripper)
    return "The robot is now inside the incubator"

def protocol_1_step_2(rtde_c, rtde_r, gripper):
    gripper.close()
    return "The robot is now gripping the object, and is now moving to the microscope"

def protocol_1_step_3(rtde_c, rtde_r, gripper):
    move_outside_incubator(rtde_c, rtde_r, gripper)
    move_to_microscope(rtde_c, rtde_r, gripper)
    return "The robot is now at the microscope, Imaging will be done now"

def protocol_1_step_4(rtde_c, rtde_r, gripper):
    gripper.open()
    time.sleep(10)
    gripper.close()
    return "Imaging complete, QC is running now"

def protocol_1_step_5(rtde_c, rtde_r, gripper):
    move_outside_incubator(rtde_c, rtde_r, gripper)
    move_inside_incubator(rtde_c, rtde_r, gripper)
    gripper.open()
    move_outside_incubator(rtde_c, rtde_r, gripper)
    return "The T-flask is back in the incubator, ending the protocol"

def protocol_1(rtde_c, rtde_r, gripper):
    protocol_1_step_1(rtde_c, rtde_r, gripper)
    protocol_1_step_2(rtde_c, rtde_r, gripper)
    protocol_1_step_3(rtde_c, rtde_r, gripper)
    protocol_1_step_4(rtde_c, rtde_r, gripper)
    protocol_1_step_5(rtde_c, rtde_r, gripper)
    return "The protocol is complete"
    

def protocol_2(rtde_c, rtde_r, gripper):
    move_outside_incubator(rtde_c, rtde_r, gripper)  # step 1
    move_inside_incubator(rtde_c, rtde_r, gripper)
    gripper.close()
    move_outside_incubator(rtde_c, rtde_r, gripper)
    move_to_microscope(rtde_c, rtde_r, gripper)
    gripper.open()
    time.sleep(10)
    gripper.close()
    move_to_decap_pose_up(rtde_c, rtde_r, gripper)
    move_to_decap_table(rtde_c, rtde_r, gripper)
    gripper.open()
    move_to_decap_away(rtde_c, rtde_r, gripper)

    move_to_fridge(rtde_c, rtde_r, gripper)
    move_to_fridge_door(rtde_c, rtde_r, gripper)
    open_fridge_door(rtde_c, rtde_r, gripper)
    back_from_fridge_door(rtde_c, rtde_r, gripper)
    move_to_away_from_reagent(rtde_c, rtde_r, gripper)
    move_to_reagent(rtde_c, rtde_r, gripper)
    gripper.close()
    move_to_away_from_reagent(rtde_c, rtde_r, gripper)
    move_to_reagent_table_away(rtde_c, rtde_r, gripper)
    move_to_reagent_table(rtde_c, rtde_r, gripper)
    gripper.open()
    move_to_reagent_table_away(rtde_c, rtde_r, gripper)
    move_to_decap_away(rtde_c, rtde_r, gripper)
    move_to_decap_table(rtde_c, rtde_r, gripper)
    gripper.close()
    move_outside_incubator(rtde_c, rtde_r, gripper)
    move_inside_incubator(rtde_c, rtde_r, gripper)
    gripper.open()
    move_outside_incubator(rtde_c, rtde_r, gripper)


def protocol_2_stream(rtde_c, rtde_r, gripper):
    """Run protocol 2 and yield (step_index, step_name, message) for streaming progress."""
    LOG.info("═══ Protocol 2 STARTED ═══")
    t0 = time.time()
    step = 0

    def emit(name, message):
        nonlocal step
        step += 1
        LOG.info("  [step %d] %s — %s", step, name, message)
        return (step, name, message)

    def do_move(fn, *args):
        try:
            fn(*args)
        except Exception as e:
            LOG.error("  [step %d] move FAILED: %s\n%s", step, e, traceback.format_exc())
            raise

    def do_gripper(action):
        try:
            _logged_gripper(action, gripper)
        except Exception as e:
            LOG.error("  [step %d] gripper.%s FAILED: %s\n%s", step, action, e, traceback.format_exc())
            raise

    def do_wait(seconds):
        LOG.debug("  waiting %.0fs ...", seconds)
        sleep(seconds)

    try:
        yield emit("move_outside_incubator", "Moving outside incubator")
        do_move(move_outside_incubator, rtde_c, rtde_r, gripper)
        yield emit("move_inside_incubator", "Moving inside incubator")
        do_move(move_inside_incubator, rtde_c, rtde_r, gripper)
        do_wait(10)
        yield emit("gripper_close", "Gripping flask")
        do_gripper("close")
        yield emit("move_outside_incubator", "Moving outside incubator")
        do_move(move_outside_incubator, rtde_c, rtde_r, gripper)
        do_wait(10)
        yield emit("move_to_microscope", "Moving to microscope")
        do_move(move_to_microscope, rtde_c, rtde_r, gripper)
        do_wait(10)
        yield emit("gripper_open", "Releasing at microscope")
        do_gripper("open")
        do_wait(10)
        yield emit("imaging", "Imaging (10s)")
        do_wait(10)
        yield emit("gripper_close", "Gripping after imaging")
        do_gripper("close")
        do_wait(10)
        yield emit("move_to_decap_pose_up", "Moving to decap position (up)")
        do_move(move_to_decap_pose_up, rtde_c, rtde_r, gripper)
        yield emit("move_to_decap_table", "Moving to decap table")
        do_move(move_to_decap_table, rtde_c, rtde_r, gripper)
        do_wait(10)
        yield emit("gripper_open", "Releasing at decap table")
        do_gripper("open")
        yield emit("move_to_decap_away", "Moving away from decap table")
        do_move(move_to_decap_away, rtde_c, rtde_r, gripper)

        yield emit("move_to_fridge", "Moving to fridge")
        do_move(move_to_fridge, rtde_c, rtde_r, gripper)
        yield emit("move_to_fridge_door", "Moving to fridge door")
        do_move(move_to_fridge_door, rtde_c, rtde_r, gripper)
        yield emit("open_fridge_door", "Opening fridge door")
        do_move(open_fridge_door, rtde_c, rtde_r, gripper)
        yield emit("back_from_fridge_door", "Back from fridge door")
        do_move(back_from_fridge_door, rtde_c, rtde_r, gripper)
        yield emit("move_to_away_from_reagent", "Moving away from reagent")
        do_move(move_to_away_from_reagent, rtde_c, rtde_r, gripper)
        yield emit("move_to_reagent", "Moving to reagent")
        do_move(move_to_reagent, rtde_c, rtde_r, gripper)
        yield emit("gripper_close", "Gripping reagent")
        do_gripper("close")
        yield emit("move_to_away_from_reagent", "Moving away from reagent")
        do_move(move_to_away_from_reagent, rtde_c, rtde_r, gripper)
        yield emit("move_to_reagent_table_away", "Moving to reagent table (away)")
        do_move(move_to_reagent_table_away, rtde_c, rtde_r, gripper)
        yield emit("move_to_reagent_table", "Moving to reagent table")
        do_move(move_to_reagent_table, rtde_c, rtde_r, gripper)
        yield emit("gripper_open", "Dispensing reagent")
        do_gripper("open")
        yield emit("move_to_reagent_table_away", "Moving away from reagent table")
        do_move(move_to_reagent_table_away, rtde_c, rtde_r, gripper)
        yield emit("move_to_decap_away", "Moving to decap (away)")
        do_move(move_to_decap_away, rtde_c, rtde_r, gripper)
        yield emit("move_to_decap_table", "Moving to decap table")
        do_move(move_to_decap_table, rtde_c, rtde_r, gripper)
        yield emit("gripper_close", "Gripping cap")
        do_gripper("close")
        yield emit("move_outside_incubator", "Moving outside incubator")
        do_move(move_outside_incubator, rtde_c, rtde_r, gripper)
        yield emit("move_inside_incubator", "Moving inside incubator (return flask)")
        do_move(move_inside_incubator, rtde_c, rtde_r, gripper)
        yield emit("gripper_open", "Releasing flask in incubator")
        do_gripper("open")
        yield emit("move_outside_incubator", "Moving outside incubator (done)")
        do_move(move_outside_incubator, rtde_c, rtde_r, gripper)
        yield emit("done", "Protocol 2 complete")

        LOG.info("═══ Protocol 2 COMPLETED (%d steps, %.1fs) ═══", step, time.time() - t0)

    except Exception as e:
        LOG.error("═══ Protocol 2 ABORTED at step %d after %.1fs: %s ═══", step, time.time() - t0, e)
        raise


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
    protocol_1(rtde_c, rtde_r, gripper)
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
    # move_to_away_from_reagent(r`tde_c, rtde_r, gripper)
    # move_outside_incubator(rtde_c, rtde_r, gripper)
    # move_to_microscope(rtde_c, rt`de_r, gripper)
    # # gripper.open()
    


if __name__ == "__main__":
    run()
