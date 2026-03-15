"""iPSC culture analysis tools — confluence, morphology, viability, experiment log.

analyze_culture: Process a microscope image → confluence %, morphology, viability.
get_experiment_log: Return accumulated culture history + event timeline.

Culture data (confluence progression, images, contamination) comes from the
active scenario loaded via `agent.providers.scenarios`.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps

_experiment_data: dict[str, dict[str, Any]] = {}


def reset_experiment_data() -> None:
    """Clear accumulated experiment data for a fresh run."""
    _experiment_data.clear()


def _get_experiment(flask_id: str) -> dict[str, Any]:
    if flask_id not in _experiment_data:
        _experiment_data[flask_id] = {
            "flask_id": flask_id,
            "cell_line": "iPSC-fast",
            "media": "Media A",
            "labware": "T75",
            "start_time": time.time(),
            "measurements": [],
            "images": [],
            "events": [],
            "feeds": 0,
        }
    return _experiment_data[flask_id]


def _get_scenario(deps: AgentDeps):
    from agent.providers.scenarios import load_scenario
    return load_scenario(deps.mock_scenario)


async def analyze_culture(
    ctx: RunContext[AgentDeps],
    image_id: str,
    flask_id: str,
    cycle_number: int,
) -> dict:
    """Analyze a microscope image for confluence percentage, colony morphology,
    viability, and contamination status.

    Call after capture_image to get quantitative culture assessment.

    Args:
        image_id: Image ID from a previous capture_image call.
        flask_id: Flask being monitored.
        cycle_number: Monitoring cycle number (1-based).
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        if cycle_number <= 1:
            _experiment_data.pop(flask_id, None)
        scenario = _get_scenario(ctx.deps)
        return _mock_analyze(
            image_id, flask_id, cycle_number,
            protocol_day=ctx.deps.protocol_day,
            culture_phase=ctx.deps.culture_phase,
            scenario=scenario,
        )

    raise NotImplementedError("Live cell analysis requires CV pipeline.")


def _mock_analyze(
    image_id: str,
    flask_id: str,
    cycle_number: int,
    protocol_day: int = 0,
    culture_phase: str = "growing",
    scenario=None,
) -> dict:
    """Simulate iPSC culture analysis using mock world state + active scenario.

    Confluence is determined by:
      - culture_phase == "growing"     → scenario.get_confluence(protocol_day)
      - culture_phase == "dissociating" → 5%
      - culture_phase == "suspended"    → 2%
      - culture_phase == "harvested"    → 0%
    """
    is_growing = culture_phase == "growing"

    if is_growing:
        confluence = scenario.get_confluence(protocol_day) if scenario else 45.0
    elif culture_phase == "dissociating":
        confluence = 5.0
    elif culture_phase == "suspended":
        confluence = 2.0
    else:
        confluence = 0.0

    # Contamination from scenario
    if scenario and is_growing:
        contam_profile = scenario.get_contamination(protocol_day)
        contamination = contam_profile.to_dict()
    elif is_growing:
        contamination = {
            "detected": False, "bacterial": False, "fungal": False,
            "mycoplasma_risk": "low", "notes": "No contamination indicators observed",
        }
    else:
        contamination = {"detected": False, "notes": "Clean suspension"}

    if is_growing:
        if contamination.get("detected"):
            morphology = {
                "colony_quality": "stressed",
                "colony_edges": "irregular, some lifting",
                "colony_packing": "disrupted",
                "differentiated_cells": "some observed",
                "cell_shape": "abnormal — signs of stress response",
            }
            viability = {
                "floating_cells": "many (abnormal)",
                "dead_cells_pct": 22.0,
                "overall": "declining",
            }
        else:
            morphology = {
                "colony_quality": "good" if confluence < 70 else "very_good",
                "colony_edges": "clean, well-defined",
                "colony_packing": "tight" if confluence > 50 else "moderate",
                "differentiated_cells": "none observed",
                "cell_shape": "typical iPSC morphology — compact, high nucleus-to-cytoplasm ratio",
            }
            viability = {
                "floating_cells": "minimal" if confluence < 60 else "few",
                "dead_cells_pct": 2.0 if confluence < 60 else 3.5,
                "overall": "healthy",
            }
    else:
        morphology = {
            "colony_quality": "n/a (dissociated)",
            "cell_shape": "rounded single cells and aggregates in suspension",
            "aggregate_size": "50–150 µm (optimal for re-plating)",
        }
        viability = {
            "floating_cells": "expected (dissociated)",
            "dead_cells_pct": 5.0,
            "overall": "good — viable aggregates",
        }

    ready_for_passage = is_growing and confluence >= 70 and not contamination.get("detected")
    needs_feeding = is_growing and confluence < 70 and not contamination.get("detected")
    cells_in_suspension = culture_phase in ("dissociating", "suspended")

    exp = _get_experiment(flask_id)
    measurement = {
        "cycle": cycle_number,
        "confluence_pct": confluence,
        "viability_pct": 100 - viability["dead_cells_pct"],
        "morphology_summary": morphology.get("colony_quality", "n/a"),
        "protocol_day": protocol_day,
        "culture_phase": culture_phase,
        "contamination_detected": contamination.get("detected", False),
        "timestamp": time.time(),
    }
    exp["measurements"].append(measurement)
    exp["images"].append({"image_id": image_id, "cycle": cycle_number})

    image_url = scenario.get_image_url(protocol_day) if scenario else "/mock-images/day0.jpg"

    all_measurements = exp["measurements"]
    history_slice = all_measurements[-3:]
    capture_history = []
    for i, m in enumerate(history_slice):
        is_current = i == len(history_slice) - 1
        m_day = m.get("protocol_day", 0)
        m_phase = m.get("culture_phase", "growing")
        capture_history.append({
            "day": m_day,
            "confluence_pct": m["confluence_pct"],
            "culture_phase": m_phase,
            "image_url": scenario.get_image_url(m_day) if scenario else "/mock-images/day0.jpg",
            "current": is_current,
        })

    recommendation = (
        "CONTAMINATION DETECTED — alert scientist immediately." if contamination.get("detected")
        else "Ready for dissociation — confluence ≥70%." if ready_for_passage
        else "Feed and continue monitoring." if needs_feeding
        else "Cells in suspension — ready for collection." if cells_in_suspension
        else "Continue monitoring."
    )

    return {
        "image_id": image_id,
        "flask_id": flask_id,
        "cycle_number": cycle_number,
        "confluence_pct": confluence,
        "morphology": morphology,
        "viability": viability,
        "contamination": contamination,
        "ready_for_passage": ready_for_passage,
        "needs_feeding": needs_feeding,
        "cells_in_suspension": cells_in_suspension,
        "protocol_day": protocol_day,
        "culture_phase": culture_phase,
        "image_url": image_url,
        "capture_history": capture_history,
        "recommendation": recommendation,
    }


async def get_experiment_log(
    ctx: RunContext[AgentDeps],
    flask_id: str,
) -> dict:
    """Return the full experiment log: confluence history, image timeline, events.

    Call this to get accumulated data across all monitoring cycles for a flask.

    Args:
        flask_id: Flask to query.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        result = _mock_experiment_log(flask_id)
        result["protocol_day"] = ctx.deps.protocol_day
        return result

    raise NotImplementedError("Live experiment log requires database connection.")


def _mock_experiment_log(flask_id: str) -> dict:
    exp = _get_experiment(flask_id)

    measurements = exp.get("measurements", [])
    if not measurements:
        measurements = [
            {"cycle": 1, "confluence_pct": 45.0, "viability_pct": 98.0, "morphology_summary": "good"},
            {"cycle": 2, "confluence_pct": 72.0, "viability_pct": 96.0, "morphology_summary": "very_good"},
        ]

    events = exp.get("events", [])
    if not events:
        events = [
            {"event": "Seeded at 12k cells/cm² (900K total) in Media A", "phase": "setup"},
            {"event": "Feed #1 — full media change, confluence 45%", "phase": "feeding"},
            {"event": "Confluence reached 72% — dissociation triggered", "phase": "dissociation"},
        ]

    latest = measurements[-1] if measurements else {}

    return {
        "flask_id": flask_id,
        "cell_line": exp.get("cell_line", "iPSC-fast"),
        "media": exp.get("media", "Media A"),
        "labware": exp.get("labware", "T75"),
        "total_cycles": len(measurements),
        "total_feeds": exp.get("feeds", 0),
        "current_confluence_pct": latest.get("confluence_pct"),
        "current_viability_pct": latest.get("viability_pct"),
        "passage_number": 12,
        "measurements": measurements,
        "events": events,
    }
