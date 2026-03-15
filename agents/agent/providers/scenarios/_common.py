"""Shared Phase 1 setup for all scenarios.

User asks: "Can you take my iPSC_fast cells, maintain them and harvest
1 billion cells in three days?"

System corrects: 1B is not feasible from a single T75 flask.
Max yield ~6.4M cells at 70% confluency. We can target 70% in 3 days
using 15k cells/cm² seeding density (1.125M starting cells).

All three scenarios share this identical Phase 1 and diverge at Phase 2.
"""

from __future__ import annotations

from typing import Any


def phase1_setup() -> list[dict[str, Any]]:
    """Return the 5-step Phase 1 pipeline shared by all scenarios."""
    return [
        {
            "tool": "check_compatibility",
            "reasoning": (
                "The scientist wants to maintain **iPSC_fast** cells and harvest "
                "**1 billion cells** in **3 days**. Let me verify compatibility — "
                "but 1 billion is far beyond what a single T75 flask can produce."
            ),
            "build_args": lambda q, r: {
                "cell_line": "iPSC_fast",
                "labware": "T75",
                "density_k_per_cm2": 15,
            },
        },
        {
            "tool": "request_human_input",
            "reasoning": (
                "**iPSC_fast** is compatible with our system. However, the requested "
                "**1 billion cells** is not achievable from a single T75 flask.\n\n"
                "**Reality check:**\n"
                "- T75 flask surface area: 75 cm²\n"
                "- At 70% confluency, max ~6.4 million cells\n"
                "- To reach 1 billion, we'd need ~156 T75 flasks\n\n"
                "We can deliver **~6.4 million cells** in **3 days** using "
                "**15,000 cells/cm²** seeding density. Presenting the adjusted plan."
            ),
            "build_args": lambda q, r: {
                "message": (
                    "**iPSC_fast confirmed compatible** with our robotic workcell.\n\n"
                    "However, **1 billion cells is not achievable** from a single T75 flask. "
                    "Here's the reality:\n\n"
                    "| Constraint | Detail |\n"
                    "|-----------|--------|\n"
                    "| Flask surface | 75 cm² |\n"
                    "| Max cells at 70% confluence | **~6.4 million** |\n"
                    "| For 1 billion cells | Need ~156 × T75 flasks |\n\n"
                    "**Adjusted proposal:** Maintain and harvest **~6.4M cells** in **3 days** "
                    "using 15k cells/cm² seeding density."
                ),
                "input_fields": [
                    {
                        "id": "density",
                        "type": "select",
                        "label": "Seeding density",
                        "options": [
                            {"value": "15", "label": "15k cells/cm² — 3 days to 70% confluency (recommended for your timeline)"},
                            {"value": "12", "label": "12k cells/cm² — 4 days to 70% confluency"},
                            {"value": "20", "label": "20k cells/cm² — 2 days to 70% confluency"},
                        ],
                        "default": "15",
                    },
                    {
                        "id": "target_cells",
                        "type": "number",
                        "label": "Target cell count (max ~6.4M from one T75)",
                        "min": 0,
                        "max": 10000000,
                        "step": 100000,
                        "unit": "cells",
                        "default": 0,
                        "required": False,
                    },
                    {
                        "id": "reseed",
                        "type": "confirm",
                        "label": "Re-seed a new flask after harvest?",
                        "default": True,
                        "confirm_label": "Yes — re-seed",
                        "deny_label": "No — harvest only",
                    },
                    {
                        "id": "notes",
                        "type": "text",
                        "label": "Special instructions",
                        "placeholder": "Any modifications or notes...",
                        "required": False,
                    },
                ],
                "info_blocks": [
                    {
                        "title": "Yield Reference (single T75 flask)",
                        "content": (
                            "| Density | Starting cells | Time to 70% | Max harvest |\n"
                            "|---------|---------------|-------------|-------------|\n"
                            "| 12k/cm² | 900K | 4 days | ~6.4M |\n"
                            "| **15k/cm²** | **1.125M** | **3 days** | **~6.4M** |\n"
                            "| 20k/cm² | 1.5M | 2 days | ~6.4M |\n\n"
                            "One T75 flask yields **~6.4 million cells** at harvest — "
                            "higher density just gets there faster."
                        ),
                        "style": "info",
                    },
                ],
            },
        },
        {
            "tool": "consult_elnora",
            "reasoning": (
                "Scientist accepted the adjusted plan: **15k cells/cm²** (1.125M starting cells) "
                "in T75, targeting 70% confluency in **3 days**, max yield ~6.4M. "
                "Consulting **Elnora AI** for expert protocol guidance."
            ),
            "build_args": lambda q, r: {
                "query": (
                    "Generate a complete iPSC maintenance, feeding, and passaging protocol "
                    "for our automated robotic workcell. "
                    "Cell line: iPSC_fast (16hr doubling time). "
                    "Media: Media A. Dissociation reagent: TrypLE Express (enzymatic). "
                    "Labware: T75 flask (75 cm² surface area). "
                    "Seeding density: 15,000 cells/cm² (1.125M total cells). "
                    "Feeding: full media change every 24 hours with 15mL Media A at room temperature. "
                    "Target: 70% confluency in 3 days. Harvest confluency: 70-80%. "
                    "Handling: fast (firm shaking after 5-7min TrypLE incubation at 37°C). "
                    "Delivery: collect into 50mL Falcon tube. "
                    "Re-seed: yes, seed new T75 at same density."
                ),
                "context": (
                    "Robot: UR12e with Robotiq gripper. "
                    "Incubator: 37°C, 5% CO₂, humidified. "
                    "Sterile work in BSC. Automated pipette station. "
                    "Zebra camera for confluence imaging. "
                    "Culture must not exceed 3 days in flask (unless authorized). "
                    "Always image BEFORE feeding."
                ),
            },
        },
        {
            "tool": "request_human_input",
            "reasoning": (
                "Elnora provided expert protocol guidance. Combined with the finalized config:\n\n"
                "**Adjusted Experiment Plan:**\n"
                "- Requested: 1 billion cells → Achievable: **~6.4M cells**\n"
                "- Starting: 15,000 × 75 = **1,125,000 cells** (1.125M)\n"
                "- Time to 70% confluency: **3 days**\n"
                "- Feeding: full media change every **24 hours** (15 mL Media A)\n"
                "- Re-seed: new T75 at 15k/cm² after harvest"
            ),
            "build_args": lambda q, r: {
                "message": (
                    "## Elnora-Informed Experiment Plan\n\n"
                    "Expert protocol guidance has been integrated with your parameters."
                ),
                "info_blocks": [
                    {
                        "title": "Protocol Summary",
                        "content": (
                            "| Parameter | Value |\n"
                            "|-----------|-------|\n"
                            "| Cell line | **iPSC_fast** (16hr doubling) |\n"
                            "| Labware | **1 × T75** (75 cm²) |\n"
                            "| Seeding density | **15,000 cells/cm²** → 1.125M starting cells |\n"
                            "| Media | **Media A**, 15 mL, full change every 24 hrs (RT) |\n"
                            "| Timeline | **3 days** to 70% confluency |\n"
                            "| Expected yield | **~6.4 million cells** |\n"
                            "| Dissociation | TrypLE → 5–7 min at 37°C → fast shaking |\n"
                            "| Delivery | **50 mL Falcon tube** |\n"
                            "| Re-seed | **Yes**, new T75 at 15k/cm² |"
                        ),
                        "style": "default",
                    },
                    {
                        "title": "Elnora Feeding Protocol",
                        "content": (
                            "1. Retrieve flask from incubator\n"
                            "2. **Image BEFORE feeding** (confluency + contamination)\n"
                            "3. Transfer to BSC\n"
                            "4. Aspirate old media → Add **15 mL fresh Media A** (RT)\n"
                            "5. Return to incubator (37°C, 5% CO₂)"
                        ),
                        "style": "info",
                    },
                    {
                        "title": "Elnora Dissociation Protocol",
                        "content": (
                            "1. Aspirate media\n"
                            "2. Wash with **5 mL DPBS** (no Ca²⁺/Mg²⁺)\n"
                            "3. Add **5 mL TrypLE**, coat surface\n"
                            "4. Incubate **5–7 min at 37°C**\n"
                            "5. **Fast shaking** to detach cells\n"
                            "6. Add **5 mL Media A** to neutralize\n"
                            "7. Collect into **50 mL Falcon**"
                        ),
                        "style": "info",
                    },
                    {
                        "title": "⚠️ Critical Constraints",
                        "content": (
                            "- Harvest when confluence reaches **70%**\n"
                            "- Max **3 days** in flask (extension requires authorization)\n"
                            "- **Always image BEFORE feeding** (contamination check)\n"
                            "- Media at **room temperature only**\n"
                            "- Flask outside incubator **≤ 15 minutes**"
                        ),
                        "style": "warning",
                    },
                    {
                        "title": "Physical Setup Required",
                        "content": (
                            "- ✅ Media A reservoir filled\n"
                            "- ✅ TrypLE bottle available\n"
                            "- ✅ DPBS bottle available\n"
                            "- ✅ Empty T75 flask (for re-seeding)\n"
                            "- ✅ 50 mL Falcon tube"
                        ),
                        "style": "success",
                    },
                ],
                "input_fields": [
                    {
                        "id": "approve",
                        "type": "confirm",
                        "label": "Approve plan and start execution?",
                        "default": True,
                        "confirm_label": "Approve & Start",
                        "deny_label": "Modify",
                    },
                ],
                "upcoming_actions": [
                    {"action": "Generate execution plan", "scope": "Build phase-by-phase step breakdown", "tool": "generate_execution_plan"},
                    {"action": "Pre-feed imaging", "scope": "Image flask for confluence", "tool": "capture_image"},
                    {"action": "Feed culture", "scope": "Aspirate + add 15 mL Media A", "tool": "pipette_aspirate + pipette_add"},
                    {"action": "Monitor until 70%", "scope": "Repeat imaging + feeding cycles", "tool": "analyze_culture"},
                    {"action": "Dissociate & deliver", "scope": "TrypLE protocol, collect, re-seed", "tool": "collect_cells"},
                ],
            },
        },
        {
            "tool": "generate_execution_plan",
            "reasoning": (
                "Scientist approved the plan. Generating a **detailed execution plan** — "
                "phase-by-phase breakdown of every robot step, tool call, and decision point."
            ),
            "build_args": lambda q, r: {
                "protocol_summary": (
                    "iPSC_fast in T75 flask, 15k cells/cm² (1.125M total), Media A 15mL, "
                    "TrypLE dissociation, 3-day timeline, harvest ~6.4M cells, re-seed"
                ),
            },
        },
    ]


def dissociation_steps() -> list[dict[str, Any]]:
    """Return the 22-step dissociation sequence shared by premature_harvest and slow_growth.

    Assumes flask is at Microscope_Stage when called.
    """
    return [
        {"tool": "pick_and_place", "reasoning": "Moving to Capping Station to decap for dissociation.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Microscope_Stage", "to_station": "Capping_Station"}},
        {"tool": "run_decap", "reasoning": "Decapping flask for wash and enzyme treatment.",
         "build_args": lambda q, r: {"flask_id": "flask_1"}},
        {"tool": "pick_and_place", "reasoning": "Moving to Harvest Station for dissociation workflow.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Capping_Station", "to_station": "Harvest_Station"}},
        {"tool": "pipette_aspirate", "reasoning": "Removing spent media — residual serum proteins inhibit TrypLE.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "spent_media", "volume_mL": 15}},
        {"tool": "pipette_add", "reasoning": "Adding **5 mL DPBS** wash to remove residual media and Ca²⁺/Mg²⁺ ions.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "DPBS", "volume_mL": 5, "source": "dpbs_bottle"}},
        {"tool": "apply_handling", "reasoning": "Gentle swirl to ensure DPBS wash covers entire growth surface.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "mode": "gentle", "duration_seconds": 30}},
        {"tool": "pipette_aspirate", "reasoning": "Aspirating DPBS wash — surface must be clean for optimal TrypLE activity.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "DPBS_wash", "volume_mL": 5}},
        {"tool": "pipette_add", "reasoning": "Adding **5 mL TrypLE Express** to digest cell adhesion proteins.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "TrypLE", "volume_mL": 5, "source": "tryple_bottle"}},
        {"tool": "pick_and_place", "reasoning": "Moving to Capping Station to recap before incubation.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Harvest_Station", "to_station": "Capping_Station"}},
        {"tool": "run_recap", "reasoning": "Sealing flask for sterile enzyme incubation.",
         "build_args": lambda q, r: {"flask_id": "flask_1"}},
        {"tool": "pick_and_place", "reasoning": "Moving to incubator for TrypLE digestion at 37°C.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Capping_Station", "to_station": "Incubator_Slot_A"}},
        {"tool": "set_incubation", "reasoning": "Timed incubation: **7 minutes at 37°C** for enzymatic digestion.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "temperature_c": 37.0, "co2_pct": 5.0, "duration_minutes": 7, "mode": "timed"}},
        {"tool": "pick_and_place", "reasoning": "Incubation complete. Moving to Shaker Platform for mechanical detachment.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Incubator_Slot_A", "to_station": "Shaker_Platform"}},
        {"tool": "apply_handling", "reasoning": "Applying **fast shaking** to dislodge enzyme-loosened cells.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "mode": "fast", "duration_seconds": 15}},
        {"tool": "pick_and_place", "reasoning": "Moving to microscope to verify cell detachment.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Shaker_Platform", "to_station": "Microscope_Stage"}},
        {"tool": "capture_image", "reasoning": "Imaging to verify cells are in suspension.",
         "build_args": lambda q, r: {"purpose": "Verify cell detachment after TrypLE + shaking", "camera_id": "microscope", "mode": "microscopy"}},
        {"tool": "analyze_culture", "reasoning": "Confirming cell detachment status.",
         "build_args": lambda q, r: {"image_id": r.get("capture_image", {}).get("image_id", "img_mock"), "flask_id": "flask_1", "cycle_number": 99}},
        {"tool": "pick_and_place", "reasoning": "Cells confirmed in suspension. Moving to Capping Station to decap for collection.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Microscope_Stage", "to_station": "Capping_Station"}},
        {"tool": "run_decap", "reasoning": "Decapping for neutralization and cell collection.",
         "build_args": lambda q, r: {"flask_id": "flask_1"}},
        {"tool": "pick_and_place", "reasoning": "Moving to Harvest Station for neutralization and cell collection.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Capping_Station", "to_station": "Harvest_Station"}},
        {"tool": "pipette_add", "reasoning": "Adding **5 mL Media A** to neutralize TrypLE and stop enzyme activity.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "Media_A", "volume_mL": 5, "source": "media_a_reservoir"}},
        {"tool": "collect_cells", "reasoning": "Collecting cell suspension into 50 mL Falcon tube.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "target_container": "falcon_50mL", "volume_mL": 10}},
    ]


def disposal_steps() -> list[dict[str, Any]]:
    """Return the 4-step cleanup: recap, dispose, final world state."""
    return [
        {"tool": "pick_and_place", "reasoning": "Moving used flask to Capping Station for recap before disposal.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Harvest_Station", "to_station": "Capping_Station"}},
        {"tool": "run_recap", "reasoning": "Sealing used flask before biosafety disposal.",
         "build_args": lambda q, r: {"flask_id": "flask_1"}},
        {"tool": "dispose_flask", "reasoning": "Disposing used flask to biohazard waste — experiment complete.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reason": "experiment_complete"}},
        {"tool": "get_world_state", "reasoning": "Capturing final workcell state for the experiment record.",
         "build_args": lambda q, r: {}},
    ]


def feed_cycle(confluence: float, reasoning_prefix: str = "") -> list[dict[str, Any]]:
    """Return the 9-step feeding sequence (decap → feed → recap → incubate).

    Assumes flask is at Microscope_Stage when called.
    """
    return [
        {"tool": "pick_and_place",
         "reasoning": f"{reasoning_prefix}Confluence at **{confluence}%**, below 70%. Moving to Capping Station for feeding.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Microscope_Stage", "to_station": "Capping_Station"}},
        {"tool": "run_decap", "reasoning": "Removing cap for media change.",
         "build_args": lambda q, r: {"flask_id": "flask_1"}},
        {"tool": "pick_and_place", "reasoning": "Moving to Feeding Station for media exchange.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Capping_Station", "to_station": "Feeding_Station"}},
        {"tool": "pipette_aspirate", "reasoning": "Aspirating spent media — metabolic waste inhibits cell growth.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "spent_media", "volume_mL": 15}},
        {"tool": "pipette_add", "reasoning": "Adding **15 mL fresh Media A** at room temperature.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "reagent": "Media_A", "volume_mL": 15, "source": "media_a_reservoir"}},
        {"tool": "pick_and_place", "reasoning": "Media changed. Moving to Capping Station to recap.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Feeding_Station", "to_station": "Capping_Station"}},
        {"tool": "run_recap", "reasoning": "Sealing flask with vented cap for CO₂ exchange during incubation.",
         "build_args": lambda q, r: {"flask_id": "flask_1"}},
        {"tool": "pick_and_place", "reasoning": "Returning capped flask to incubator within 15-min limit.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Capping_Station", "to_station": "Incubator_Slot_A"}},
        {"tool": "set_incubation", "reasoning": "Flask back in incubator. 37°C, 5% CO₂, continuous until next feed cycle.",
         "build_args": lambda q, r: {"flask_id": "flask_1", "temperature_c": 37.0, "co2_pct": 5.0, "mode": "continuous"}},
    ]


def check_cycle(cycle: int, purpose: str) -> list[dict[str, Any]]:
    """Return the 3-step imaging sub-sequence (pick_and_place → capture → analyze)."""
    return [
        {"tool": "pick_and_place",
         "reasoning": f"Moving flask to microscope — {purpose}.",
         "build_args": lambda q, r: {"object_id": "flask_1", "from_station": "Incubator_Slot_A", "to_station": "Microscope_Stage"}},
        {"tool": "capture_image",
         "reasoning": f"Capturing confluence image — cycle {cycle}.",
         "build_args": lambda q, r: {"purpose": f"Confluence check — cycle {cycle}", "camera_id": "microscope", "mode": "microscopy"}},
        {"tool": "analyze_culture",
         "reasoning": "Analyzing confluence, morphology, viability, contamination.",
         "build_args": lambda q, r: {
             "image_id": r.get("capture_image", {}).get("image_id", "img_mock"),
             "flask_id": "flask_1", "cycle_number": cycle}},
    ]
