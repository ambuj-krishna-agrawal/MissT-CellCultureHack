"""Elnora AI integration — consult Elnora for protocol expertise.

Uses the Elnora CLI to create tasks, send messages, and read AI-generated
protocol recommendations. Always calls the live Elnora API regardless of
mock_mode (Elnora is a knowledge service, not hardware).

Supports multi-turn: consult_elnora creates a task, follow_up_elnora
continues the conversation on the same task.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from typing import Any

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps

LOG = logging.getLogger(__name__)

_ELNORA_BIN: str | None = None


def _find_elnora_bin() -> str | None:
    """Locate the elnora CLI binary."""
    global _ELNORA_BIN
    if _ELNORA_BIN is not None:
        return _ELNORA_BIN or None

    path = shutil.which("elnora")
    if path:
        _ELNORA_BIN = path
        return path

    for candidate in [
        "/Library/Frameworks/Python.framework/Versions/3.11/bin/elnora",
        os.path.expanduser("~/.local/bin/elnora"),
    ]:
        if os.path.isfile(candidate):
            _ELNORA_BIN = candidate
            return candidate

    _ELNORA_BIN = ""
    return None


async def _run_elnora(*args: str) -> dict[str, Any]:
    """Execute an elnora CLI command and return parsed JSON."""
    binary = _find_elnora_bin()
    if not binary:
        raise RuntimeError("elnora CLI not found. Install with: pip install elnora")

    env = os.environ.copy()
    api_key = env.get("ELNORA_API_KEY", "")
    if not api_key:
        from dotenv import dotenv_values
        vals = dotenv_values()
        api_key = vals.get("ELNORA_API_KEY", "")
        if api_key:
            env["ELNORA_API_KEY"] = api_key

    cmd = [binary, "--compact"] + list(args)
    LOG.info("Elnora CLI: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err_text = stderr.decode().strip() or stdout.decode().strip()
        LOG.error("Elnora CLI error (code %d): %s", proc.returncode, err_text)
        try:
            return json.loads(err_text)
        except json.JSONDecodeError:
            return {"error": err_text, "code": f"EXIT_{proc.returncode}"}

    try:
        return json.loads(stdout.decode())
    except json.JSONDecodeError:
        return {"raw_output": stdout.decode().strip()}


_cached_project_id: str | None = None


async def _ensure_project() -> str:
    """Get or create the CellPilot project in Elnora."""
    global _cached_project_id
    if _cached_project_id:
        return _cached_project_id

    result = await _run_elnora("projects", "list")
    items = result.get("items", [])
    for proj in items:
        if "cellpilot" in proj.get("name", "").lower():
            _cached_project_id = proj["id"]
            return _cached_project_id

    create_result = await _run_elnora(
        "projects", "create", "--name", "CellPilot Protocols",
    )
    pid = create_result.get("id")
    if pid:
        _cached_project_id = pid
        return pid

    raise RuntimeError(f"Failed to create Elnora project: {create_result}")


async def _poll_for_response(task_id: str) -> dict[str, Any]:
    """Poll Elnora task for an assistant response (up to ~3 min)."""
    max_polls = 60
    poll_interval = 3.0
    for attempt in range(max_polls):
        await asyncio.sleep(poll_interval)
        messages = await _run_elnora("tasks", "messages", task_id)
        items = messages.get("items", [])
        ai_msgs = [m for m in items if m.get("role") == "assistant"]
        if ai_msgs:
            latest = ai_msgs[-1]
            LOG.info(
                "Elnora responded after %d polls (%.0fs)",
                attempt + 1, (attempt + 1) * poll_interval,
            )
            return {
                "source": "elnora",
                "status": "success",
                "task_id": task_id,
                "protocol_text": latest.get("content", ""),
                "message_id": latest.get("id", ""),
            }

    return {
        "source": "elnora",
        "status": "timeout",
        "task_id": task_id,
        "waited_seconds": max_polls * poll_interval,
    }


# ── Tools ────────────────────────────────────────────────────────────────────

async def consult_elnora(
    ctx: RunContext[AgentDeps],
    query: str,
    context: str | None = None,
) -> dict:
    """Consult Elnora AI for protocol expertise and recommendations.

    Creates a new task in Elnora and returns the AI-generated protocol.
    Use this for initial protocol questions. For follow-up refinements
    on the same protocol, use follow_up_elnora with the returned task_id.

    Args:
        query: Natural language protocol question or request.
        context: Optional additional context (organism, conditions, constraints).
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        return _mock_consult()
    return await _live_consult(query, context)


async def follow_up_elnora(
    ctx: RunContext[AgentDeps],
    task_id: str,
    message: str,
) -> dict:
    """Send a follow-up message on an existing Elnora task.

    Use this to iterate on a protocol — e.g. request modifications,
    add steps, change parameters. The conversation history is preserved
    so Elnora has full context.

    Args:
        task_id: The task_id returned from a previous consult_elnora call.
        message: Follow-up message or modification request.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        return _mock_follow_up(task_id)
    return await _live_follow_up(task_id, message)


async def _live_consult(query: str, context: str | None) -> dict:
    """Create a task in Elnora, send the query, and poll for the response."""
    project_id = await _ensure_project()

    full_message = query + "\n\nIMPORTANT: Please provide your response in **markdown format** with proper headers, tables, numbered lists, and bold emphasis for key values."
    if context:
        full_message = f"{query}\n\nContext: {context}\n\nIMPORTANT: Please provide your response in **markdown format** with proper headers, tables, numbered lists, and bold emphasis for key values."

    title = query[:80] if len(query) <= 80 else query[:77] + "..."
    task_result = await _run_elnora(
        "tasks", "create",
        "--project", project_id,
        "--title", title,
        "--message", full_message,
    )

    if "error" in task_result:
        return {"source": "elnora", "status": "error", "error": task_result["error"]}

    task_id = task_result.get("id")
    if not task_id:
        return {"source": "elnora", "status": "error", "error": "No task ID returned", "raw": task_result}

    return await _poll_for_response(task_id)


async def _live_follow_up(task_id: str, message: str) -> dict:
    """Send a follow-up message on an existing Elnora task."""
    full_msg = message + "\n\nPlease respond in **markdown format**."
    send_result = await _run_elnora(
        "tasks", "send", task_id,
        "--message", full_msg,
    )

    if "error" in send_result:
        return {"source": "elnora", "status": "error", "error": send_result["error"], "task_id": task_id}

    return await _poll_for_response(task_id)


# ── Mock ─────────────────────────────────────────────────────────────────────
# Uses the actual Elnora response captured during testing.

_MOCK_PROTOCOL_TEXT = (
    "# Automated iPSC-fast Passaging and Harvest Protocol\n\n"
    "## Objective\n"
    "To achieve maximum cell yield (**~6.4M cells**) over a 3-day culture period "
    "using the **iPSC-fast** cell line in a **T75 flask**. This protocol utilizes "
    "an automated workcell, enzymatic dissociation (TrypLE Express), and room-temperature "
    "media to maintain cell viability and pluripotency while strictly adhering to "
    "time-out-of-incubator constraints.\n\n"
    "---\n\n"
    "## Key Parameters & Critical Constraints\n\n"
    "| Parameter | Value |\n"
    "| :--- | :--- |\n"
    "| **Cell Line** | iPSC-fast (Doubling time: **~16 hours**) |\n"
    "| **Labware** | 1x T75 flask (**75 cm\u00b2**) |\n"
    "| **Seeding Density** | **12,000 cells/cm\u00b2** (**900K total cells**) |\n"
    "| **Target Yield** | **~6.4M cells** at Day 4 |\n"
    "| **Media** | Media A (**ROOM TEMPERATURE ONLY** - Do **NOT** warm) |\n"
    "| **Dissociation Reagent** | TrypLE Express (Enzymatic) |\n"
    "| **Feeding Schedule** | Every **24 hours** (Full media change, **15 mL**) |\n"
    "| **Confluency Limits** | Max before passage: **70%** \\| Target at harvest: **80%** |\n"
    "| **Time Constraint** | Flask must **NOT exceed 15 minutes** outside the incubator |\n\n"
    "---\n\n"
    "## Materials & Equipment\n\n"
    "### Reagents & Consumables\n"
    "*   **Media A** (Equilibrated to Room Temperature)\n"
    "*   **TrypLE Express** Dissociation Reagent\n"
    "*   **D-PBS** (without Ca\u00b2\u207a and Mg\u00b2\u207a)\n"
    "*   T75 Tissue Culture Treated Flasks\n"
    "*   **50 mL** Falcon Tubes\n"
    "*   Sterile pipette tips (compatible with automated pipette station)\n\n"
    "### Workcell Equipment\n"
    "*   UR12e Robot Arm with Robotiq Gripper\n"
    "*   Automated Pipette Station\n"
    "*   Automated CO\u2082 Incubator (**37\u00b0C, 5% CO\u2082**)\n"
    "*   Biological Safety Cabinet (BSC)\n"
    "*   Automated Microscope / Imaging Station\n\n"
    "---\n\n"
    "## 4-Day Schedule Overview\n\n"
    "| Day | Action | Target Confluency | Media Volume |\n"
    "| :--- | :--- | :--- | :--- |\n"
    "| **Day 0** | Initial Seeding | ~10-15% | **15 mL** |\n"
    "| **Day 1** | Daily Feed (24h) | ~25-35% | **15 mL** |\n"
    "| **Day 2** | Daily Feed (48h) | ~50-60% | **15 mL** |\n"
    "| **Day 3** | Daily Feed (72h) | ~65-70% | **15 mL** |\n"
    "| **Day 4** | Harvest & Re-seed (96h) | **80%** | **15 mL** (New Flask) |\n\n"
    "---\n\n"
    "## Step-by-Step Procedure\n\n"
    "### Part 1: Daily Feeding (Days 1–3)\n"
    "*Execute every 24 hours. Ensure the entire cycle completes in **< 15 minutes**.*\n\n"
    "1.  **Retrieve Flask:** UR12e robot arm transfers the T75 flask from the "
    "**37\u00b0C incubator** to the microscope.\n"
    "2.  **Image & QC:** Capture images to verify confluency.\n"
    "    *   *Note: Confluency must remain **< 70%** during the growth phase to "
    "prevent spontaneous differentiation.*\n"
    "3.  **Transfer to BSC:** Move the flask to the pipette station inside the BSC.\n"
    "4.  **Aspirate Media:** Completely aspirate the spent media from the flask.\n"
    "5.  **Add Fresh Media:** Dispense **15 mL** of **Room Temperature Media A** "
    "gently against the side of the flask to avoid disturbing the cell monolayer.\n"
    "6.  **Return to Incubator:** UR12e robot arm transfers the flask back to the "
    "**37\u00b0C, 5% CO\u2082** incubator.\n\n"
    "### Part 2: Harvest & Dissociation (Day 4)\n"
    "*Execute at 96 hours post-seeding. Target confluency is **80%**.*\n\n"
    "1.  **Retrieve & Verify:** Transfer the T75 flask to the microscope. "
    "Verify confluency has reached the **80%** target.\n"
    "2.  **Transfer to BSC:** Move the flask to the pipette station.\n"
    "3.  **Aspirate Media:** Completely aspirate the spent media.\n"
    "4.  **DPBS Wash:** Add **5 mL** D-PBS to rinse residual media and serum. "
    "Aspirate the wash.\n"
    "5.  **Add TrypLE:** Dispense **5 mL** of TrypLE Express into the flask, "
    "ensuring the entire cell layer is covered.\n"
    "6.  **Incubate:** Transfer the flask to the **37\u00b0C incubator** for "
    "**5 to 7 minutes**.\n"
    "7.  **Mechanical Detachment:** Retrieve the flask from the incubator. "
    "Use the robot arm/shaker to perform **fast shaking** to dislodge "
    "detached cells.\n"
    "8.  **Neutralize & Resuspend:** Add **5 mL** of **Room Temperature Media A** "
    "to neutralize TrypLE. Wash the growth surface to collect detached cells.\n"
    "9.  **Collection:** Transfer the 10 mL cell suspension into a sterile "
    "**50 mL Falcon tube**.\n\n"
    "### Part 3: Cell Counting & Re-seeding (Day 4)\n\n"
    "1.  **Count Cells:** Take a small aliquot from the **50 mL Falcon tube** "
    "to determine cell concentration and total yield (Expected yield: **~6.4M cells**).\n"
    "2.  **Calculate Seeding Volume:** Calculate the volume of cell suspension "
    "required to obtain exactly **900K cells** (for a seeding density of "
    "**12,000 cells/cm\u00b2**).\n"
    "3.  **Prepare New Flask:**\n"
    "    *   Transfer the calculated cell volume into a **new T75 flask**.\n"
    "    *   Add **Room Temperature Media A** to bring the final volume in the "
    "flask to exactly **15 mL**.\n"
    "4.  **Distribute Cells:** Gently rock the flask (cross-motion: left-to-right, "
    "top-to-bottom) to ensure even distribution of cells.\n"
    "5.  **Incubate:** Transfer the new T75 flask to the **37\u00b0C, 5% CO\u2082** incubator.\n"
    "6.  **Store/Process Remaining Cells:** The remaining cells in the **50 mL "
    "Falcon tube** (~5.5M cells) are now ready for downstream assays, "
    "cryopreservation, or delivery.\n\n"
    "---\n\n"
    "## Troubleshooting & Critical Notes\n\n"
    "*   **Temperature Shock Prevention:** iPSC-fast cells are sensitive to "
    "temperature fluctuations. The strict adherence to **Room Temperature Media A** "
    "prevents the degradation of heat-sensitive factors in the media, while the "
    "**< 15 minute** out-of-incubator rule prevents the flask from cooling excessively.\n"
    "*   **TrypLE Timing:** Incubate for exactly **5–7 minutes**. Over-incubation "
    "can reduce viability. Under-incubation leaves cells attached. Monitor detachment "
    "by imaging after shaking.\n"
    "*   **Fast Shaking:** If cells do not detach after the 5-7 minute incubation "
    "and fast shaking, re-incubate for 2 additional minutes and shake again. "
    "Do *not* add more TrypLE."
)


def _mock_consult() -> dict:
    return {
        "source": "elnora",
        "status": "success",
        "task_id": "mock_task_85da3e1c",
        "protocol_text": _MOCK_PROTOCOL_TEXT,
        "message_id": "mock_msg_5cc0810d",
    }


def _mock_follow_up(task_id: str) -> dict:
    return {
        "source": "elnora",
        "status": "success",
        "task_id": task_id,
        "protocol_text": (
            "## Follow-Up Recommendation\n\n"
            "Based on the current culture conditions, I recommend:\n\n"
            "1. **Continue daily feeding** with 15 mL Room Temperature Media A\n"
            "2. **Monitor confluency** — if approaching 70%, consider early passage\n"
            "3. **Maintain incubator conditions** at 37°C, 5% CO₂\n\n"
            "No protocol modifications are needed at this time."
        ),
        "message_id": "mock_msg_follow_up_001",
    }
