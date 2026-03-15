"""Robot SSE streaming client.

Connects to the robot server's /protocol/2 endpoint, streams events into
an async queue, and lets tools drain events in sync with the physical robot.

One feeding cycle = one /protocol/2 call = 32 events.
Tools consume events via checkpoints so the UI step matches the robot state.

When no robot URL is configured (mock mode), a MockRobotStreamClient replays
hardcoded events with configurable delay so the UI still shows "Robot Live".
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Awaitable, Callable

import requests

LOG = logging.getLogger(__name__)

# Each checkpoint is the last robot event number a tool should drain to.
# Mapped sequentially to the order tools are called in a feeding cycle.
CHECKPOINTS = [6, 7, 11, 12, 20, 24, 26, 27, 30, 32]

DRAIN_TOOLS = frozenset({
    "pick_and_place", "capture_image", "run_decap", "run_recap",
    "pipette_add", "set_incubation",
})

# Hardcoded protocol-2 events captured from the real UR12e robot.
# Used by MockRobotStreamClient when no ngrok URL is present.
MOCK_ROBOT_EVENTS: list[dict[str, Any]] = [
    {"step": 1,  "name": "move_outside_incubator",    "message": "UR12e approaching incubator (37°C, 5% CO₂)"},
    {"step": 2,  "name": "move_inside_incubator",     "message": "Reaching into incubator — locating T75 flask"},
    {"step": 3,  "name": "gripper_close",             "message": "Robotiq gripper secured on flask"},
    {"step": 4,  "name": "move_outside_incubator",    "message": "Extracting flask from incubator"},
    {"step": 5,  "name": "move_to_microscope",        "message": "Transporting flask to Zebra microscope station"},
    {"step": 6,  "name": "gripper_open",              "message": "Flask positioned on microscope stage"},
    {"step": 7,  "name": "imaging",                   "message": "Capturing confluency image — phase-contrast microscopy"},
    {"step": 8,  "name": "gripper_close",             "message": "Retrieving flask from microscope"},
    {"step": 9,  "name": "move_to_decap_pose_up",     "message": "Navigating to capping station — approach vector"},
    {"step": 10, "name": "move_to_decap_table",       "message": "Positioning flask in decapping fixture"},
    {"step": 11, "name": "gripper_open",              "message": "Flask seated — initiating cap removal"},
    {"step": 12, "name": "move_to_decap_away",        "message": "Cap removed — clearing capping station"},
    {"step": 13, "name": "move_to_fridge",            "message": "Navigating to reagent refrigerator (4°C)"},
    {"step": 14, "name": "move_to_fridge_door",       "message": "Approaching fridge door mechanism"},
    {"step": 15, "name": "open_fridge_door",          "message": "Opening refrigerator — accessing Media A"},
    {"step": 16, "name": "back_from_fridge_door",     "message": "Door held open — preparing to retrieve reagent"},
    {"step": 17, "name": "move_to_away_from_reagent", "message": "Aligning with Media A bottle position"},
    {"step": 18, "name": "move_to_reagent",           "message": "Reaching for Media A (15 mL, room temp equilibrated)"},
    {"step": 19, "name": "gripper_close",             "message": "Media A bottle secured in gripper"},
    {"step": 20, "name": "move_to_away_from_reagent", "message": "Extracting Media A from refrigerator"},
    {"step": 21, "name": "move_to_reagent_table_away","message": "Transporting media to feeding station"},
    {"step": 22, "name": "move_to_reagent_table",     "message": "Positioning at automated pipette station"},
    {"step": 23, "name": "gripper_open",              "message": "Dispensing 15 mL fresh Media A into flask"},
    {"step": 24, "name": "move_to_reagent_table_away","message": "Media change complete — clearing pipette station"},
    {"step": 25, "name": "move_to_decap_away",        "message": "Returning to capping station with flask cap"},
    {"step": 26, "name": "move_to_decap_table",       "message": "Aligning cap with flask opening"},
    {"step": 27, "name": "gripper_close",             "message": "Cap re-sealed — sterile closure confirmed"},
    {"step": 28, "name": "move_outside_incubator",    "message": "Transporting flask back to incubator"},
    {"step": 29, "name": "move_inside_incubator",     "message": "Placing flask in incubator (37°C, 5% CO₂, humidified)"},
    {"step": 30, "name": "gripper_open",              "message": "Flask released on incubator shelf"},
    {"step": 31, "name": "move_outside_incubator",    "message": "Arm retracting — incubator door closing"},
    {"step": 32, "name": "done",                      "message": "Feeding cycle complete — culture secured in incubator"},
]

# Real robot takes ~80s for 32 events → ~2.5s per event.
# In mock mode we compress it, scaled by mock_delay.
_MOCK_EVENT_INTERVAL = 0.4  # seconds between events (default, overridden by mock_delay)


class RobotStreamClient:
    """Manages a single robot protocol streaming connection."""

    def __init__(self, robot_url: str):
        self.robot_url = robot_url.rstrip("/")
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._thread: threading.Thread | None = None
        self._checkpoint_idx = 0
        self._started = False
        self._finished = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._all_events: list[dict[str, Any]] = []

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=self._stream_worker, daemon=True)
        self._thread.start()
        LOG.info("Robot stream started → %s", self.robot_url)

    def _stream_worker(self) -> None:
        """Background thread: POST /robot/init then stream /protocol/2."""
        try:
            session = requests.Session()

            headers = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true",
            }

            init_resp = session.post(
                f"{self.robot_url}/robot/init",
                headers=headers,
                timeout=30,
            )
            init_data = init_resp.json()
            if not init_data.get("ok"):
                LOG.warning("Robot init failed: %s", init_data)
                self._finished = True
                return

            LOG.info("Robot initialized, starting protocol/2 stream")
            resp = session.post(
                f"{self.robot_url}/protocol/2",
                headers={**headers, "Accept": "text/event-stream"},
                stream=True,
                timeout=300,
            )

            if resp.status_code != 200:
                LOG.warning("Robot protocol/2 returned %d: %s", resp.status_code, resp.text[:200])
                self._finished = True
                return

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                    self._all_events.append(event)
                    if self._loop:
                        self._loop.call_soon_threadsafe(self.queue.put_nowait, event)
                    if event.get("name") == "done":
                        break
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            LOG.error("Robot stream error: %s", e)
        finally:
            self._finished = True
            LOG.info("Robot stream finished (%d events)", len(self._all_events))

    async def drain_next(
        self,
        callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> list[dict[str, Any]]:
        """Drain events up to the next checkpoint, forwarding each via callback."""
        if self._checkpoint_idx >= len(CHECKPOINTS):
            return []

        target = CHECKPOINTS[self._checkpoint_idx]
        self._checkpoint_idx += 1
        events: list[dict[str, Any]] = []

        while True:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=60.0)
                events.append(event)
                if callback:
                    await callback(event)
                if event.get("step", 0) >= target:
                    break
            except asyncio.TimeoutError:
                LOG.warning("Robot stream drain timeout at checkpoint %d", target)
                break

        return events

    def should_drain(self, tool_name: str) -> bool:
        return (
            tool_name in DRAIN_TOOLS
            and self._started
            and self._checkpoint_idx < len(CHECKPOINTS)
        )

    def reset(self) -> None:
        self._started = False
        self._finished = False
        self._checkpoint_idx = 0
        self.queue = asyncio.Queue()
        self._all_events.clear()
        self._thread = None
        self._loop = None


class MockRobotStreamClient:
    """Replays hardcoded robot events with timed delays — no real robot needed."""

    def __init__(self, event_interval: float = _MOCK_EVENT_INTERVAL):
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._checkpoint_idx = 0
        self._started = False
        self._finished = False
        self._event_interval = event_interval
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._task = asyncio.ensure_future(self._replay_events())
        LOG.info("Mock robot stream started (%d events, %.2fs interval)",
                 len(MOCK_ROBOT_EVENTS), self._event_interval)

    async def _replay_events(self) -> None:
        """Feed hardcoded events into the queue with delays."""
        try:
            for event in MOCK_ROBOT_EVENTS:
                await asyncio.sleep(self._event_interval)
                self.queue.put_nowait(dict(event))
        except Exception as e:
            LOG.error("Mock robot replay error: %s", e)
        finally:
            self._finished = True
            LOG.info("Mock robot stream finished (32 events)")

    async def drain_next(
        self,
        callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> list[dict[str, Any]]:
        """Drain events up to the next checkpoint, forwarding each via callback."""
        if self._checkpoint_idx >= len(CHECKPOINTS):
            return []

        target = CHECKPOINTS[self._checkpoint_idx]
        self._checkpoint_idx += 1
        events: list[dict[str, Any]] = []

        while True:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=30.0)
                events.append(event)
                if callback:
                    await callback(event)
                if event.get("step", 0) >= target:
                    break
            except asyncio.TimeoutError:
                LOG.warning("Mock robot drain timeout at checkpoint %d", target)
                break

        return events

    def should_drain(self, tool_name: str) -> bool:
        return (
            tool_name in DRAIN_TOOLS
            and self._started
            and self._checkpoint_idx < len(CHECKPOINTS)
        )

    def reset(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._started = False
        self._finished = False
        self._checkpoint_idx = 0
        self.queue = asyncio.Queue()
        self._task = None


async def drain_robot_if_active(
    deps: Any,
    tool_name: str,
) -> bool:
    """Drain robot events for this tool if a robot stream is active.

    Returns True if events were drained (caller should skip mock_pause).
    """
    robot_stream: RobotStreamClient | MockRobotStreamClient | None = deps.state.get("_robot_stream")
    if robot_stream and robot_stream.should_drain(tool_name):
        callback = deps.state.get("_robot_event_callback")
        await robot_stream.drain_next(callback)
        return True
    return False


def maybe_start_robot_stream(deps: Any) -> None:
    """Start a robot stream. Uses real URL if configured, otherwise mock events."""
    existing: RobotStreamClient | MockRobotStreamClient | None = deps.state.get("_robot_stream")
    if existing and existing._started:
        return

    robot_url = deps.robot_stream_url
    if robot_url:
        client: RobotStreamClient | MockRobotStreamClient = RobotStreamClient(robot_url)
    elif deps.mock_mode:
        interval = max(deps.mock_delay, 0.05) if deps.mock_delay > 0 else _MOCK_EVENT_INTERVAL
        client = MockRobotStreamClient(event_interval=interval)
    else:
        return

    deps.state["_robot_stream"] = client
    client.start()
