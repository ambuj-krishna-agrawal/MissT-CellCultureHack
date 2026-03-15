"""Scenario 2: Contamination Detected

Cells got contaminated on Day 1.
- Day 0: 15% confluence, culture looks normal
- Day 1: 5% confluence — debris visible, media turned yellow from red
- Alert user → dispose flask → start new batch quickly
- No harvest — experiment terminated
- Images: A1-0 (clean, 15%), A1-1 (contaminated, 5%)
"""

from __future__ import annotations

from typing import Any

from agent.providers.scenarios.base import ContaminationProfile, Scenario
from agent.providers.scenarios._common import phase1_setup


def _pipeline() -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []

    # ── Phase 1: Setup & Configuration (shared) ──────────────────────────
    steps += phase1_setup()

    # ── Phase 2: Monitoring & Feeding ─────────────────────────────────────
    steps.append({
        "tool": "load_phase_plan",
        "reasoning": "Loading **Phase 2: Culture Monitoring & Feeding** steps.",
        "build_args": lambda q, r: {"phase": "phase_2"},
    })
    steps.append({
        "tool": "get_world_state",
        "reasoning": "Starting **Monitoring Cycle 1.** Verifying workcell state.",
        "build_args": lambda q, r: {},
    })
    steps.append({
        "tool": "pick_and_place",
        "reasoning": "Moving flask to microscope for pre-feed imaging.",
        "build_args": lambda q, r: {
            "object_id": "flask_1",
            "from_station": "Incubator_Slot_A",
            "to_station": "Microscope_Stage",
        },
    })
    steps.append({
        "tool": "capture_image",
        "reasoning": "Capturing pre-feed confluence image — cycle 1.",
        "build_args": lambda q, r: {
            "purpose": "Pre-feed confluence and viability assessment — cycle 1",
            "camera_id": "microscope",
            "mode": "microscopy",
        },
    })
    steps.append({
        "tool": "analyze_culture",
        "reasoning": "Analyzing image for confluence, morphology, viability, and contamination screening.",
        "build_args": lambda q, r: {
            "image_id": r.get("capture_image", {}).get("image_id", "img_mock"),
            "flask_id": "flask_1",
            "cycle_number": 1,
        },
    })

    # ── CONTAMINATION DETECTED ────────────────────────────────────────────
    steps.append({
        "tool": "request_human_input",
        "reasoning": (
            "## ⚠️ CONTAMINATION ALERT\n\n"
            "Analysis detected **contamination** in flask_1!\n\n"
            "**Visual evidence:**\n"
            "- **Debris visible** in the culture — floating particles and aggregates\n"
            "- **Media color changed from red to yellow** — indicates pH drop from "
            "microbial metabolic acid production\n"
            "- Confluence **dropped** from 15% (Day 0) to **5%** — cells dying/detaching\n"
            "- Cells showing signs of stress: irregular colony edges, lifting\n\n"
            "The culture is **unusable**. Recommending immediate disposal to prevent "
            "cross-contamination. A new batch should be started quickly."
        ),
        "build_args": lambda q, r: {
            "message": (
                "## ⚠️ Contamination Detected — Flask Compromised\n\n"
                "**Visual evidence:**\n"
                "- **Debris visible** — floating particles and dark aggregates in media\n"
                "- **Media turned yellow** (was red) — pH dropped due to microbial acid production\n"
                "- Confluence **dropped** from 15% to **5%** — cells are dying\n"
                "- Cell colonies show stress: irregular edges, some lifting from surface\n\n"
                "| Metric | Value |\n"
                "|--------|-------|\n"
                "| Confluence | **5%** (was 15% at seeding) |\n"
                "| Contamination | **Detected — debris + yellow media** |\n"
                "| Viability | 78% (declining rapidly) |\n"
                "| Morphology | Stressed — irregular edges, lifting |\n"
                "| Media color | **Yellow** (normal: red/pink) |"
            ),
            "info_blocks": [
                {
                    "title": "⚠️ Immediate Action Required",
                    "content": (
                        "- This flask is **contaminated and unusable**\n"
                        "- Continuing risks **cross-contamination** of incubator and other cultures\n"
                        "- **Dispose immediately** and start a new batch\n"
                        "- The sooner we dispose and restart, the less time is lost"
                    ),
                    "style": "warning",
                },
            ],
            "input_fields": [
                {
                    "id": "action",
                    "type": "select",
                    "label": "How to proceed?",
                    "options": [
                        {"value": "abort", "label": "Dispose flask and start new batch (recommended)"},
                        {"value": "continue", "label": "Continue monitoring (risk accepted)"},
                    ],
                    "default": "abort",
                },
            ],
        },
    })

    # Scientist chooses abort → dispose
    steps.append({
        "tool": "pick_and_place",
        "reasoning": (
            "Scientist chose to **dispose immediately**. Moving contaminated flask from "
            "microscope to Capping Station to seal before disposal."
        ),
        "build_args": lambda q, r: {
            "object_id": "flask_1",
            "from_station": "Microscope_Stage",
            "to_station": "Capping_Station",
        },
    })
    steps.append({
        "tool": "run_recap",
        "reasoning": "Sealing contaminated flask to contain debris and prevent spills during disposal.",
        "build_args": lambda q, r: {"flask_id": "flask_1"},
    })
    steps.append({
        "tool": "dispose_flask",
        "reasoning": (
            "Disposing contaminated flask to biohazard waste. Workcell will be ready for "
            "a **new batch** once decontamination is verified."
        ),
        "build_args": lambda q, r: {"flask_id": "flask_1", "reason": "contamination_detected"},
    })
    steps.append({
        "tool": "get_world_state",
        "reasoning": "Verifying workcell is clear and ready for a new batch.",
        "build_args": lambda q, r: {},
    })

    return steps


SCENARIO = Scenario(
    name="contamination",
    description=(
        "Contamination detected on Day 1 — debris visible, media turned yellow from red. "
        "Confluence dropped from 15% to 5%. Flask disposed to start new batch quickly."
    ),
    pipeline=_pipeline(),
    completion={
        "summary": (
            "iPSC_fast culture **terminated due to contamination** detected on Day 1. "
            "Debris was visible in the culture and media color changed from **red to yellow**, "
            "indicating microbial acid production. Confluence dropped from 15% to **5%** — "
            "cells were dying. Flask disposed to biohazard waste. "
            "No cells harvested. Workcell is clear — ready to **start a new batch**."
        ),
        "status": "aborted",
        "next_steps": [
            "Start a new batch immediately — workcell is clear",
            "Investigate contamination source (media prep, hood sterility, incubator)",
            "Check media lot — yellow discoloration indicates pH drop",
            "Perform incubator decontamination cycle before next run",
        ],
        "key_findings": [
            "Contamination detected at Day 1 — confluence dropped from 15% to 5%",
            "Evidence: debris visible in media, color changed from red to yellow",
            "Yellow media = pH drop from microbial metabolic acid production",
            "Cell viability had dropped to 78% at time of detection",
            "Flask disposed per biosafety protocol — workcell cleared for new batch",
        ],
    },
    day_to_confluence={0: 15.0, 1: 5.0},
    day_to_image={
        0: "/mock-images/contamination/day0.jpg",
        1: "/mock-images/contamination/day1.jpg",
    },
    contamination_by_day={
        1: ContaminationProfile(
            detected=True,
            bacterial=True,
            fungal=False,
            mycoplasma_risk="unknown",
            notes=(
                "Debris visible — floating particles and dark aggregates in media. "
                "Media color changed from red to yellow, indicating pH drop from "
                "microbial metabolic acid production. Confluence dropped from 15% "
                "to 5% — cells dying and detaching. Colonies showing stress with "
                "irregular edges and lifting."
            ),
        ),
    },
)
