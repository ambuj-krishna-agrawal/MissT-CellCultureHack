"""Scenario data structure.

Each scenario bundles everything needed to simulate a complete
iPSC experiment run with deterministic mock data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ContaminationProfile:
    """Per-day contamination result."""
    detected: bool = False
    bacterial: bool = False
    fungal: bool = False
    mycoplasma_risk: str = "low"
    notes: str = "No contamination indicators observed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "bacterial": self.bacterial,
            "fungal": self.fungal,
            "mycoplasma_risk": self.mycoplasma_risk,
            "notes": self.notes,
        }


@dataclass
class Scenario:
    """Complete mock scenario definition."""

    name: str
    description: str

    # Mock LLM pipeline — list of tool-call steps (same shape as current PIPELINE)
    pipeline: list[dict[str, Any]] = field(default_factory=list)

    # Final completion message when pipeline ends
    completion: dict[str, Any] = field(default_factory=dict)

    # Culture progression: protocol_day → confluence %
    day_to_confluence: dict[int, float] = field(default_factory=dict)

    # Image URLs served from ui/public: protocol_day → URL path
    day_to_image: dict[int, str] = field(default_factory=dict)

    # Contamination profile per protocol_day (days not listed use default_contamination)
    contamination_by_day: dict[int, ContaminationProfile] = field(default_factory=dict)

    # Fallback contamination result
    default_contamination: ContaminationProfile = field(
        default_factory=ContaminationProfile
    )

    def get_confluence(self, protocol_day: int) -> float:
        if protocol_day in self.day_to_confluence:
            return self.day_to_confluence[protocol_day]
        last_known = max(self.day_to_confluence.keys()) if self.day_to_confluence else 0
        return min(95.0, self.day_to_confluence.get(last_known, 15.0) + (protocol_day - last_known) * 15.0)

    def get_image_url(self, protocol_day: int) -> str:
        if protocol_day in self.day_to_image:
            return self.day_to_image[protocol_day]
        max_day = max(self.day_to_image.keys()) if self.day_to_image else 0
        return self.day_to_image.get(max_day, "/mock-images/day0.jpg")

    def get_contamination(self, protocol_day: int) -> ContaminationProfile:
        return self.contamination_by_day.get(protocol_day, self.default_contamination)
