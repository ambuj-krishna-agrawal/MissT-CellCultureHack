# Standalone UR scripts (no ROS, no Docker)

Scripts to move the robot and control the Robotiq gripper from a laptop.

**Two options:**

1. **Raw socket (no extra deps)** – URScript to port 30001 for motion; ASCII commands to port 63352 for gripper.
2. **ur_rtde (SDU Robotics)** – RTDE interface for motion; gripper still uses port 63352 (same as SDU’s RobotiqGripper example). Install: `pip install ur-rtde`.

## Prerequisites

- Python 3.6+
- Robot and laptop on the same network (see below)
- **Socket scripts:** E-series in **Remote Control** mode so port 30001 accepts commands
- **ur_rtde scripts:** By default ur_rtde uploads its control script to the robot (no program on pendant). Use `--external-control` if you run the External Control URCap program on the pendant.

## Commands to run (copy-paste)

### 1. Network setup (one-time)

**On the robot teach pendant**

- **Setup Robot → Network**
- Set a static IP, e.g. `192.168.56.101`
- Subnet: `255.255.255.0`, Gateway: `192.168.56.1`

**On the laptop**

- Set the Ethernet interface to the same subnet, e.g. IP `192.168.56.1`, netmask `255.255.255.0`

**Check connectivity**

```bash
ping -c 3 192.168.56.101
```

### 2. Run the script (default left/right poses)

```bash
cd /path/to/CellCultureHack/standalone
python3 ur_left_right.py 192.168.56.101
```

(Replace `192.168.56.101` with your robot’s IP.)

### 3. Slower motion

```bash
python3 ur_left_right.py 192.168.56.101 --velocity 0.05
```

### 4. Custom left/right poses (x,y,z,rx,ry,rz in m and rad)

```bash
python3 ur_left_right.py 192.168.56.101 \
  --left-pose "0.3,0.1,0.3,3.14,0,0" \
  --right-pose "0.3,-0.1,0.3,3.14,0,0"
```

### 5. Different port (if your setup uses Secondary Interface)

```bash
python3 ur_left_right.py 192.168.56.101 --port 30002
```

### 6. Make the script executable and run

```bash
chmod +x ur_left_right.py
./ur_left_right.py 192.168.56.101
```

---

## Using ur_rtde (SDU Robotics)

Motion uses the RTDE interface instead of raw URScript. The gripper still uses the Robotiq URCap socket (port 63352); SDU’s own [RobotiqGripper example](https://sdurobotics.gitlab.io/ur_rtde/_static/robotiq_gripper.py) uses the same protocol.

**Install**

```bash
pip install -r requirements.txt
# or
pip install ur-rtde
```

**Arm motion: moveL, moveJ, speedJ**

Default is **moveL** (Cartesian left/right poses). You can use **moveJ** (joint targets) or **speedJ** (joint velocities) as in the [ur_rtde examples](https://sdurobotics.gitlab.io/ur_rtde/examples/examples.html):

```bash
# moveL (default)
python3 ur_left_right_rtde.py 192.168.56.101
python3 ur_left_right_rtde.py 192.168.56.101 --velocity 0.05

# moveJ: joint-space targets (rad)
python3 ur_left_right_rtde.py 192.168.56.101 --mode movej
python3 ur_left_right_rtde.py 192.168.56.101 --mode movej --left-joints "0,-0.5,0.5,0,0.5,0" --right-joints "0,-0.5,0.5,0,-0.5,0"

# speedJ: joint velocities for a duration (rad/s)
python3 ur_left_right_rtde.py 192.168.56.101 --mode speedj --speedj "0.05,0,0,0,0,0" --speedj-duration 2.0
```

With External Control URCap (program running on pendant):

```bash
python3 ur_left_right_rtde.py 192.168.56.101 --external-control
```

**Gripper** (unchanged: port 63352)

```bash
python3 ur_gripper.py 192.168.56.101 activate
python3 ur_gripper.py 192.168.56.101 open
python3 ur_gripper.py 192.168.56.101 close
```

**Combined demo** (motion via ur_rtde + gripper via 63352)

```bash
python3 ur_demo_rtde.py 192.168.56.101
```

| Script                  | Motion        | Gripper   |
|-------------------------|---------------|-----------|
| ur_left_right.py        | Socket 30001 (movel URScript) | – |
| ur_left_right_rtde.py   | ur_rtde: moveL / moveJ / speedJ | – |
| ur_gripper.py           | –             | Socket 63352 |
| ur_demo_rtde.py         | ur_rtde       | Socket 63352 |

---

## Summary

| Step            | Command |
|-----------------|--------|
| Check network   | `ping -c 3 192.168.56.101` |
| Default motion (socket) | `python3 ur_left_right.py 192.168.56.101` |
| Default motion (ur_rtde) | `pip install ur-rtde` then `python3 ur_left_right_rtde.py 192.168.56.101` |
| Slower          | `python3 ur_left_right.py 192.168.56.101 --velocity 0.05` |
| Custom poses    | `python3 ur_left_right.py ROBOT_IP --left-pose "x,y,z,rx,ry,rz" --right-pose "..."` |

## Gripper (Robotiq 2F-85)

The Robotiq 2F-85 is controlled via the **Robotiq Gripper URCap** installed on the robot. The URCap runs a small socket server on the **robot’s IP, port 63352**. Use the standalone script below; no ROS or Docker needed.

**Prerequisite:** Install the [Robotiq Gripper URCap](https://www.robotiq.com/support/2f-85-2f-140) on the robot (Setup Robot → URCaps). The gripper must be connected (e.g. to the tool flange) and powered.

### Gripper commands (copy-paste)

Replace `192.168.56.101` with your robot’s IP.

**Activate the gripper (do this once after power-on)**

```bash
python3 ur_gripper.py 192.168.56.101 activate
```

**Open (fully)**

```bash
python3 ur_gripper.py 192.168.56.101 open
```

**Close (fully)**

```bash
python3 ur_gripper.py 192.168.56.101 close
```

**Move to a specific position (0 = open, 255 = closed)**

```bash
python3 ur_gripper.py 192.168.56.101 pos 128
```

**Read current position**

```bash
python3 ur_gripper.py 192.168.56.101 get-pos
```

**Read status / object detection**

```bash
python3 ur_gripper.py 192.168.56.101 get-sta
python3 ur_gripper.py 192.168.56.101 get-obj
```

### Gripper summary

| Action   | Command |
|----------|---------|
| Activate | `python3 ur_gripper.py ROBOT_IP activate` |
| Open     | `python3 ur_gripper.py ROBOT_IP open` |
| Close    | `python3 ur_gripper.py ROBOT_IP close` |
| Position | `python3 ur_gripper.py ROBOT_IP pos 0-255` |
| Get pos  | `python3 ur_gripper.py ROBOT_IP get-pos` |

The server expects one ASCII command per line (e.g. `SET ACT 1`, `SET POS 255`, `GET POS`). Other options: `SET SPE`, `SET FOR`, `GET STA`, `GET OBJ` (see Robotiq socket documentation).

---

## Safety

- Ensure the workspace is clear and the physical **Stop** is within reach.
- Default poses are conservative; adjust `--left-pose` / `--right-pose` to match your cell and mounting.
