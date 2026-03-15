"""iPSC media and compatibility tools — seeding math and cell line validation."""

from __future__ import annotations

from typing import Any

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps

CELL_LINES = {
    "iPSC-fast": {
        "compatible_media": ["Media A"],
        "dissociation_reagent": "TrypLE",
        "doubling_time_hrs": 16,
        "feeding_schedule_hrs": 24,
        "optimal_harvest_confluency_pct": 80,
        "passage_confluency_pct": 70,
        "handling": "fast",
    },
}

LABWARE = {
    "T75": {
        "surface_area_cm2": 75,
        "density_range_k_per_cm2": (12, 20),
        "system_compatible": True,
        "media_volume_mL": 15,
    },
    "T25": {
        "surface_area_cm2": 25,
        "density_range_k_per_cm2": (8, 16),
        "system_compatible": False,
    },
}

DENSITY_TO_CONFLUENCY_DAYS = {
    10: {"days": 5, "demo_hours": 5},
    12: {"days": 4, "demo_hours": 4},
    15: {"days": 3, "demo_hours": 3},
    20: {"days": 2, "demo_hours": 2},
}


async def check_compatibility(
    ctx: RunContext[AgentDeps],
    cell_line: str,
    labware: str,
    density_k_per_cm2: int = 12,
) -> dict:
    """Check if a cell line, labware, and seeding density combination is compatible.

    Validates media, dissociation reagent, density range, and system support.

    Args:
        cell_line: Cell line name (e.g. "iPSC-fast").
        labware: Labware type (e.g. "T75").
        density_k_per_cm2: Seeding density in thousands of cells per cm².
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()

    warnings: list[dict[str, str]] = []
    checks_passed: list[str] = []

    cl = CELL_LINES.get(cell_line)
    if not cl:
        return {
            "compatible": False,
            "cell_line": cell_line,
            "error": f"Unknown cell line '{cell_line}'. Available: {list(CELL_LINES.keys())}",
        }

    lw = LABWARE.get(labware)
    if not lw:
        return {
            "compatible": False,
            "labware": labware,
            "error": f"Unknown labware '{labware}'. Available: {list(LABWARE.keys())}",
        }

    if not lw.get("system_compatible"):
        warnings.append({
            "severity": "critical",
            "message": f"{labware} is not currently system-compatible. Use T75.",
        })
    else:
        checks_passed.append(f"{labware} is system-compatible")

    lo, hi = lw["density_range_k_per_cm2"]
    if density_k_per_cm2 < lo or density_k_per_cm2 > hi:
        warnings.append({
            "severity": "warning",
            "message": f"Density {density_k_per_cm2}k/cm² is outside recommended range ({lo}–{hi}k) for {labware}.",
        })
    else:
        checks_passed.append(f"Density {density_k_per_cm2}k/cm² is within range ({lo}–{hi}k)")

    surface_area = lw["surface_area_cm2"]
    total_cells = density_k_per_cm2 * 1000 * surface_area
    time_info = DENSITY_TO_CONFLUENCY_DAYS.get(density_k_per_cm2, {"days": 4, "demo_hours": 4})

    compatible = all(w["severity"] != "critical" for w in warnings)

    return {
        "compatible": compatible,
        "cell_line": cell_line,
        "labware": labware,
        "media": cl["compatible_media"][0],
        "dissociation_reagent": cl["dissociation_reagent"],
        "handling": cl["handling"],
        "doubling_time_hrs": cl["doubling_time_hrs"],
        "feeding_schedule_hrs": cl["feeding_schedule_hrs"],
        "harvest_confluency_pct": cl["optimal_harvest_confluency_pct"],
        "passage_confluency_pct": cl["passage_confluency_pct"],
        "surface_area_cm2": surface_area,
        "seeding_density_k_per_cm2": density_k_per_cm2,
        "total_cells_to_seed": total_cells,
        "media_volume_mL": lw.get("media_volume_mL", 15),
        "time_to_70pct_confluency_days": time_info["days"],
        "demo_time_hours": time_info["demo_hours"],
        "warnings": warnings,
        "checks_passed": checks_passed,
        "protocol_day": ctx.deps.protocol_day,
    }


async def calculate_media_volumes(
    ctx: RunContext[AgentDeps],
    labware: str,
    operation: str,
    num_flasks: int = 1,
) -> dict:
    """Calculate media and reagent volumes for iPSC culture operations.

    Args:
        labware: Labware type (e.g. "T75").
        operation: One of "feed" (media change), "dissociation" (TrypLE), "reseed" (new flask).
        num_flasks: Number of flasks (default 1).
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()

    lw = LABWARE.get(labware, LABWARE["T75"])
    media_vol_mL = lw.get("media_volume_mL", 15)

    day = ctx.deps.protocol_day

    if operation == "feed":
        return {
            "operation": "feed",
            "labware": labware,
            "num_flasks": num_flasks,
            "media_to_remove_mL": media_vol_mL * num_flasks,
            "fresh_media_mL": media_vol_mL * num_flasks,
            "media_type": "Media A",
            "total_media_needed_mL": media_vol_mL * num_flasks,
            "notes": "Full media change. Aspirate spent media to waste, add fresh Media A at room temperature.",
            "protocol_day": day,
        }
    elif operation == "dissociation":
        return {
            "operation": "dissociation",
            "labware": labware,
            "num_flasks": num_flasks,
            "tryple_volume_mL": 5.0 * num_flasks,
            "dpbs_wash_mL": 5.0 * num_flasks,
            "neutralization_media_mL": 5.0 * num_flasks,
            "reagent": "TrypLE",
            "protocol": "DPBS wash → add TrypLE → incubate 37°C 5–7 min → shake to detach → neutralize with equal volume media",
            "notes": "Enzymatic dissociation. Produces single-cell suspension for counting and harvest.",
            "protocol_day": day,
        }
    elif operation == "reseed":
        surface_area = lw["surface_area_cm2"]
        return {
            "operation": "reseed",
            "labware": labware,
            "num_flasks": num_flasks,
            "fresh_media_mL": media_vol_mL * num_flasks,
            "surface_area_cm2": surface_area,
            "media_type": "Media A",
            "notes": f"Seed at target density into {labware} with {media_vol_mL} mL Media A.",
            "protocol_day": day,
        }

    return {"error": f"Unknown operation '{operation}'. Use 'feed', 'dissociation', or 'reseed'."}
