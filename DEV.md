# Development

Local setup for contributors. End-user run instructions stay in `README.md`.

## Environment (Pixi, Python 3.8)

Install [Pixi](https://pixi.sh), then from the repo root:

```bash
pixi lock    # if pixi.lock is missing or deps changed
pixi install
```

Activate the env (optional):

```bash
pixi shell
```

Run with the pinned env without activating:

```bash
pixi run python ur_left_right.py <robot_ip>
pixi run python ur_left_right_rtde.py <robot_ip>
# task shortcut (pass args after --)
pixi run ur-left-right -- <robot_ip>
```

## Environment (pip only)

If you prefer a plain venv:

```bash
python3.8 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Socket-only scripts (`ur_left_right.py`, etc.) need no extra packages. RTDE scripts need `ur-rtde` (included in `requirements.txt` and Pixi).

## Layout

- Root Python entrypoints: `ur_*.py`, `robotiq_gripper.py`, `ur_gripper.py`
- `requirements.txt` – minimal pip deps for RTDE flows

## Lockfile

Commit `pixi.lock` after changing `pixi.toml` so installs are reproducible. Regenerate with `pixi lock`.
