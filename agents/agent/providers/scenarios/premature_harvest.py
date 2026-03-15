"""Scenario 1: Premature Harvest

Cells grew faster than expected — need to harvest early.
Confluence target was 70% in a maximum of 3 days.
- Day 0: 15% confluence (seeded)
- Day 1: 35% confluence → feed (ahead of schedule)
- Day 2: 75% confluence → harvest early (only Day 2 of 3-day plan)
- Re-seed leftovers to enable "cells on tap"
- Yield: 6.2M cells, 95.5% viability
- Images: A1-0 (15%), A1-2 (35%), A1-5 (75%)
"""

from __future__ import annotations

from typing import Any

from agent.providers.scenarios.base import Scenario
from agent.providers.scenarios._common import (
    phase1_setup,
    feed_cycle,
    dissociation_steps,
    disposal_steps,
)


def _pipeline() -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []

    # ── Phase 1: Setup & Configuration (shared) ──────────────────────────
    steps += phase1_setup()

    # ── Phase 2: Monitoring & Feeding ─────────────────────────────────────
    steps.append({
        "tool": "load_phase_plan",
        "reasoning": (
            "Execution plan generated. Loading **Phase 2: Culture "
            "Monitoring & Feeding** — daily imaging, confluence assessment, "
            "feeding cycles, and incubation."
        ),
        "build_args": lambda q, r: {"phase": "phase_2"},
    })

    # ── Cycle 1: Day 1 — 35% confluence → feed (ahead of schedule) ──────
    steps.append({
        "tool": "get_world_state",
        "reasoning": (
            "Phase 2 steps loaded. Starting **Monitoring Cycle 1.** "
            "Verifying workcell state — flask location, incubator status, robot readiness."
        ),
        "build_args": lambda q, r: {},
    })
    steps.append({
        "tool": "pick_and_place",
        "reasoning": (
            "Workcell verified: flask_1 in Incubator_Slot_A, all stations available, "
            "robot idle. Moving flask to microscope for pre-feed imaging."
        ),
        "build_args": lambda q, r: {
            "object_id": "flask_1",
            "from_station": "Incubator_Slot_A",
            "to_station": "Microscope_Stage",
        },
    })
    steps.append({
        "tool": "capture_image",
        "reasoning": "Flask on microscope stage. Capturing pre-feed confluence image.",
        "build_args": lambda q, r: {
            "purpose": "Pre-feed confluence and viability assessment — cycle 1",
            "camera_id": "microscope",
            "mode": "microscopy",
        },
    })
    steps.append({
        "tool": "analyze_culture",
        "reasoning": (
            "Image captured. Analyzing for confluence %, morphology, viability, "
            "and contamination. If confluence < 70% → feed. If ≥ 70% → dissociate."
        ),
        "build_args": lambda q, r: {
            "image_id": r.get("capture_image", {}).get("image_id", "img_mock"),
            "flask_id": "flask_1",
            "cycle_number": 1,
        },
    })

    # 35% < 70% → feed (but growing faster than expected!)
    steps += feed_cycle(
        35.0,
        "Confluence at **35%** — already higher than expected for Day 1 "
        "(predicted ~23%). Cells are growing **faster than expected**. ",
    )

    # ── Cycle 2: Day 2 — 75% confluence → harvest! ──────────────────────
    steps.append({
        "tool": "pick_and_place",
        "reasoning": (
            "Feed cycle complete. Given the rapid growth yesterday (35% on Day 1 "
            "vs expected ~23%), cells may already be near threshold. "
            "Moving flask for confluence check."
        ),
        "build_args": lambda q, r: {
            "object_id": "flask_1",
            "from_station": "Incubator_Slot_A",
            "to_station": "Microscope_Stage",
        },
    })
    steps.append({
        "tool": "capture_image",
        "reasoning": "Capturing post-incubation confluence image — cycle 2.",
        "build_args": lambda q, r: {
            "purpose": "Post-incubation confluence check — cycle 2",
            "camera_id": "microscope",
            "mode": "microscopy",
        },
    })
    steps.append({
        "tool": "analyze_culture",
        "reasoning": "Analyzing confluence — with the rapid growth rate, cells may have already crossed 70%.",
        "build_args": lambda q, r: {
            "image_id": r.get("capture_image", {}).get("image_id", "img_mock"),
            "flask_id": "flask_1",
            "cycle_number": 2,
        },
    })

    # ── Phase 3: Dissociation & Delivery ──────────────────────────────────
    steps.append({
        "tool": "load_phase_plan",
        "reasoning": (
            "Culture reached **75%** confluency on **Day 2** — that's only 2 days into "
            "the 3-day plan! Cells grew faster than expected. Need to harvest "
            "early. Loading **Phase 3: Dissociation & Delivery**."
        ),
        "build_args": lambda q, r: {"phase": "phase_3"},
    })
    steps.append({
        "tool": "request_human_input",
        "reasoning": (
            "Phase 3 loaded. Confluence reached **75%** on **Day 2** — well ahead of "
            "the 3-day timeline!\n\n"
            "**Premature harvest situation:**\n"
            "- Expected: 70% confluency by Day 3\n"
            "- Actual: **75%** confluency by **Day 2** (1 day early!)\n"
            "- Growth rate: ~150% of expected\n"
            "- Morphology: excellent ✓\n"
            "- Contamination: none ✓\n\n"
            "Need to harvest now before cells overgrow. Leftovers will be re-seeded "
            "to enable **cells on tap** for future experiments."
        ),
        "build_args": lambda q, r: {
            "message": (
                "## ⚡ Early Harvest Required\n\n"
                "Cells grew **faster than expected** — reached **75% confluency** on **Day 2** "
                "(expected by Day 3).\n\n"
                "| Metric | Expected | Actual |\n"
                "|--------|----------|--------|\n"
                "| Day 1 | ~23% | **35%** |\n"
                "| Day 2 | ~47% | **75%** ✅ |\n"
                "| Target day | Day 3 | **Day 2** |\n\n"
                "**Pre-dissociation assessment:**\n"
                "- Colony morphology: tightly packed, clean edges ✅\n"
                "- Viability: 96% ✅\n"
                "- Contamination: none detected ✅\n\n"
                "Leftovers will be re-seeded to enable **cells on tap**."
            ),
            "info_blocks": [
                {
                    "title": "⚠️ Irreversible Step",
                    "content": (
                        "Dissociation will **permanently detach** all cells from the flask. "
                        "This cannot be undone. Cells will be collected into a 50 mL Falcon.\n\n"
                        "Leftover cells will be re-seeded into a fresh T75 at 15k/cm² to maintain "
                        "a **cells-on-tap** supply for future experiments."
                    ),
                    "style": "warning",
                },
            ],
            "input_fields": [
                {
                    "id": "proceed",
                    "type": "select",
                    "label": "How to proceed?",
                    "options": [
                        {"value": "dissociate", "label": "Start dissociation — cells are ready"},
                        {"value": "feed_wait", "label": "Feed & wait — let them grow more"},
                        {"value": "cancel", "label": "Cancel — do not proceed"},
                    ],
                    "default": "dissociate",
                },
            ],
            "upcoming_actions": [
                {"action": "Decap flask", "scope": "Open at Capping Station", "tool": "run_decap"},
                {"action": "DPBS wash", "scope": "Wash with 5 mL DPBS", "tool": "pipette_add"},
                {"action": "Add TrypLE", "scope": "5 mL enzyme", "tool": "pipette_add"},
                {"action": "Incubate", "scope": "37°C, 7 minutes", "tool": "set_incubation"},
                {"action": "Fast shaking", "scope": "Dislodge cells", "tool": "apply_handling"},
                {"action": "Collect cells", "scope": "Transfer to 50 mL Falcon", "tool": "collect_cells"},
            ],
        },
    })

    # Dissociation sequence
    steps += dissociation_steps()

    # Collection notification
    steps.append({
        "tool": "request_human_input",
        "reasoning": "Cells collected! Notifying scientist with yield and viability data.",
        "build_args": lambda q, r: {
            "message": (
                "## ✅ Cells Ready for Collection — Early Harvest\n\n"
                "| Metric | Value |\n"
                "|--------|-------|\n"
                "| Total cells | **6.2M** |\n"
                "| Viability | **95.5%** |\n"
                "| Efficiency | **96.9%** |\n"
                "| Container | 50 mL Falcon tube |\n"
                "| Location | Harvest Station |\n"
                "| Harvested on | **Day 2** (1 day early) |\n\n"
                "Leftover cells will be re-seeded into a fresh T75 for **cells on tap**.\n\n"
                "Please pick up the falcon tube."
            ),
            "input_fields": [
                {"id": "collected", "type": "confirm", "label": "I have picked up the falcon tube",
                 "default": True, "confirm_label": "Collected", "deny_label": "Not yet"},
            ],
        },
    })

    # Cleanup
    steps += disposal_steps()

    return steps


SCENARIO = Scenario(
    name="premature_harvest",
    description=(
        "Cells grew faster than expected — harvested on Day 2 instead of Day 3. "
        "Leftovers re-seeded for cells-on-tap."
    ),
    pipeline=_pipeline(),
    completion={
        "summary": (
            "iPSC_fast culture **harvested early on Day 2** (expected Day 3). Cells grew "
            "~150% faster than expected — 15% → 35% → 75% confluency in just 2 days. "
            "**6.2M cells** collected into 50 mL Falcon (95.5% viability, 96.9% efficiency). "
            "Leftovers re-seeded into fresh T75 for **cells on tap**. Flask disposed."
        ),
        "status": "completed",
        "next_steps": [
            "Process collected cells per downstream protocol",
            "Cells are in 50 mL Falcon at Harvest Station — pick up soon",
            "Re-seeded T75 flask is in incubator — cells on tap for next experiment",
            "Monitor re-seeded flask; expect faster-than-typical growth again",
        ],
        "key_findings": [
            "Cells grew ~150% faster than expected — 75% confluency on Day 2 (target was Day 3)",
            "Day 1: 35% (expected ~23%) — early indicator of accelerated growth",
            "Day 2: 75% — 1 day ahead of schedule",
            "6.2M cells collected, 95.5% viability, 96.9% efficiency",
            "Leftovers re-seeded for cells-on-tap pipeline",
            "No contamination detected throughout",
        ],
    },
    day_to_confluence={0: 15.0, 1: 35.0, 2: 75.0},
    day_to_image={
        0: "/mock-images/premature_harvest/day0.jpg",
        1: "/mock-images/premature_harvest/day1.jpg",
        2: "/mock-images/premature_harvest/day2.jpg",
    },
)
