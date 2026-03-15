"""Scenario 3: Slow Growth

Cells growing slower than expected — need to authorize an extra day.
Confluence target was 70% in max 3 days.
- Day 0: 15% confluence (seeded)
- Day 1:  5% confluence → feed (poor initial attachment)
- Day 2: 35% confluence → feed (recovering but behind)
- Day 3: 55% confluence → max days reached! Ask user to authorize extra day
- Day 4: 75% confluence → harvest (after authorized extra day)
- Yield: 5.8M cells, 93.2% viability (slightly lower due to extended culture)
- Images: A1-0 (15%), A1-1 (5%), A1-2 (35%), A1-3 (55%), A1-5 (75%)
"""

from __future__ import annotations

from typing import Any

from agent.providers.scenarios.base import Scenario
from agent.providers.scenarios._common import (
    phase1_setup,
    feed_cycle,
    check_cycle,
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
        "reasoning": "Loading **Phase 2: Culture Monitoring & Feeding** steps.",
        "build_args": lambda q, r: {"phase": "phase_2"},
    })

    # ── Cycle 1: Day 1 — 5% confluence → feed (terrible attachment) ──────
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
            "purpose": "Pre-feed confluence assessment — cycle 1",
            "camera_id": "microscope",
            "mode": "microscopy",
        },
    })
    steps.append({
        "tool": "analyze_culture",
        "reasoning": (
            "Analyzing culture. Confluence expected ~23% for Day 1 but "
            "result may show poor initial attachment."
        ),
        "build_args": lambda q, r: {
            "image_id": r.get("capture_image", {}).get("image_id", "img_mock"),
            "flask_id": "flask_1",
            "cycle_number": 1,
        },
    })
    steps += feed_cycle(
        5.0,
        "Confluence at only **5%** — significantly below expected ~23% for Day 1. "
        "Very poor initial attachment. Growth is **much slower than expected**. ",
    )

    # ── Cycle 2: Day 2 — 35% confluence → feed (recovering) ─────────────
    steps += check_cycle(2, "cycle 2 check")
    steps[-1]["reasoning"] = (
        "Confluence at **35%** — cells are recovering from poor attachment but still "
        "behind schedule (expected ~47% by Day 2). Continuing to feed."
    )
    steps += feed_cycle(35.0, "Recovering but still behind. ")

    # ── Cycle 3: Day 3 — 55% confluence → MAX DAYS REACHED ──────────────
    steps += check_cycle(3, "Day 3 — final scheduled check")
    steps[-1]["reasoning"] = (
        "Confluence at **55%** on **Day 3** — the maximum scheduled duration. "
        "Still **15% below** the 70% target. Growth rate has been slower than expected "
        "throughout. Need to ask the scientist to authorize an **extra day**."
    )
    steps.append({
        "tool": "request_human_input",
        "reasoning": (
            "## ⏰ Maximum Duration Reached\n\n"
            "We've hit **Day 3** — the maximum scheduled protocol duration — but confluence "
            "is only **55%**, still 15% below the 70% target.\n\n"
            "**Growth summary:**\n"
            "| Day | Confluence | Expected |\n"
            "|-----|-----------|----------|\n"
            "| 0 | 15% | 15% |\n"
            "| 1 | 5% | ~23% |\n"
            "| 2 | 35% | ~47% |\n"
            "| 3 | 55% | ≥70% |\n\n"
            "The cells are healthy but growing slowly — poor initial attachment set them back. "
            "One more day should get us above 70%. Requesting authorization."
        ),
        "build_args": lambda q, r: {
            "message": (
                "## ⏰ Day 3 Reached — Below Target\n\n"
                "Confluence is **55%** — still **15% below** the 70% target.\n"
                "The protocol was scheduled for a maximum of **3 days**, which is now reached.\n\n"
                "| Day | Confluence | Expected | Delta |\n"
                "|-----|-----------|----------|-------|\n"
                "| 0 | 15% | 15% | — |\n"
                "| 1 | 5% | ~23% | -18% |\n"
                "| 2 | 35% | ~47% | -12% |\n"
                "| 3 | **55%** | **≥70%** | **-15%** |\n\n"
                "Cells are **healthy** — no contamination, good morphology — just growing slowly "
                "due to poor initial attachment on Day 1."
            ),
            "info_blocks": [
                {
                    "title": "Assessment",
                    "content": (
                        "- Morphology: normal iPSC colonies, clean edges\n"
                        "- Viability: 97% (good)\n"
                        "- No contamination\n"
                        "- Poor initial attachment (5% on Day 1 vs expected 23%)\n"
                        "- Recovery since Day 1 has been steady: 5% → 35% → 55%\n\n"
                        "**One more day** should bring confluence above 70% based on current trajectory."
                    ),
                    "style": "info",
                },
            ],
            "input_fields": [
                {
                    "id": "action",
                    "type": "select",
                    "label": "Authorize extra day?",
                    "options": [
                        {"value": "authorize_extra", "label": "Yes — authorize 1 extra day (recommended)"},
                        {"value": "harvest_now", "label": "Harvest now at 55% (lower yield)"},
                        {"value": "abort", "label": "Abort — dispose flask"},
                    ],
                    "default": "authorize_extra",
                },
            ],
        },
    })

    # Scientist authorizes extra day → feed cycle
    steps += feed_cycle(55.0, "Extra day authorized. ")

    # ── Cycle 4: Day 4 — 75% confluence → ready! ─────────────────────────
    steps += check_cycle(4, "Day 4 (authorized extra day)")
    steps[-1]["reasoning"] = (
        "Confluence at **75%** — above 70% threshold! The extra day paid off. "
        "Ready for dissociation."
    )

    # ── Phase 3: Dissociation & Delivery ──────────────────────────────────
    steps.append({
        "tool": "load_phase_plan",
        "reasoning": (
            "Culture reached **75%** on Day 4 (authorized extra day). "
            "Loading Phase 3: Dissociation & Delivery."
        ),
        "build_args": lambda q, r: {"phase": "phase_3"},
    })
    steps.append({
        "tool": "request_human_input",
        "reasoning": "Confluence reached **75%** after 4 days (1 extra). Confirming dissociation.",
        "build_args": lambda q, r: {
            "message": (
                "## Ready for Dissociation\n\n"
                "Culture reached **75% confluency** on **Day 4** (1 extra day authorized).\n\n"
                "| Metric | Value |\n"
                "|--------|-------|\n"
                "| Confluence | 75% (≥70% ✓) |\n"
                "| Morphology | Good — colonies healthy |\n"
                "| Viability | 94.5% |\n"
                "| Contamination | None |\n"
                "| Growth rate | Slow but steady — recovered from poor attachment |\n"
                "| Total days | 4 (1 extra authorized) |"
            ),
            "info_blocks": [
                {
                    "title": "⚠️ Irreversible Step",
                    "content": (
                        "Dissociation will permanently detach all cells. "
                        "Cells will be collected into 50 mL Falcon tube."
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
                        {"value": "dissociate", "label": "Start dissociation"},
                        {"value": "cancel", "label": "Cancel"},
                    ],
                    "default": "dissociate",
                },
            ],
        },
    })

    # Dissociation sequence
    steps += dissociation_steps()

    # Collection notification
    steps.append({
        "tool": "request_human_input",
        "reasoning": "Cells collected. Yield slightly lower due to slow growth.",
        "build_args": lambda q, r: {
            "message": (
                "## ✅ Cells Ready for Collection\n\n"
                "| Metric | Value |\n"
                "|--------|-------|\n"
                "| Total cells | **5.8M** |\n"
                "| Viability | **93.2%** |\n"
                "| Efficiency | **94.1%** |\n"
                "| Container | 50 mL Falcon tube |\n"
                "| Location | Harvest Station |\n"
                "| Total days | **4** (1 extra authorized) |\n"
                "| Note | Slightly lower yield due to slow growth |\n\n"
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
    name="slow_growth",
    description=(
        "Slower-than-expected iPSC growth — poor initial attachment (5% Day 1), "
        "3 feeding cycles + 1 authorized extra day to reach 75% confluency on Day 4."
    ),
    pipeline=_pipeline(),
    completion={
        "summary": (
            "iPSC_fast culture completed with **slower-than-expected growth**. Poor initial "
            "attachment resulted in only 5% confluence on Day 1 (expected ~23%). Cells recovered "
            "steadily: 5% → 35% → 55%, but required **4 days** (1 extra authorized) to reach "
            "75% confluency. **5.8M cells** collected into 50 mL Falcon (93.2% viability, "
            "94.1% efficiency)."
        ),
        "status": "completed",
        "next_steps": [
            "Process collected cells — viability is acceptable despite slow growth",
            "Investigate slow growth: initial attachment was very poor (5% on Day 1)",
            "Consider increasing seeding density to 20k/cm² for next run",
            "Check flask coating and media lot — poor attachment suggests surface issue",
        ],
        "key_findings": [
            "Very poor initial attachment: 5% on Day 1 (expected ~23%)",
            "Steady recovery after Day 1: 5% → 35% → 55% → 75%",
            "Required 1 extra authorized day (4 total) to reach 75% confluency",
            "Cells remained healthy throughout — no contamination, good morphology",
            "5.8M cells collected, 93.2% viability, 94.1% efficiency",
            "Recommendation: investigate flask coating or increase seeding density",
        ],
    },
    day_to_confluence={0: 15.0, 1: 5.0, 2: 35.0, 3: 55.0, 4: 75.0},
    day_to_image={
        0: "/mock-images/slow_growth/day0.jpg",
        1: "/mock-images/slow_growth/day1.jpg",
        2: "/mock-images/slow_growth/day2.jpg",
        3: "/mock-images/slow_growth/day3.jpg",
        4: "/mock-images/slow_growth/day4.jpg",
    },
)
