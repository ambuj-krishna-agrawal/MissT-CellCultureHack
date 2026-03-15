"""Mock scenario loader.

Each scenario defines the full mock pipeline (LLM tool-call sequence),
culture progression data, contamination behavior, and image mappings.

Config key: tools.mock_scenario  (default: "premature_harvest")
"""

from __future__ import annotations

from typing import Any

from agent.providers.scenarios.base import Scenario

_REGISTRY: dict[str, str] = {
    "premature_harvest": "agent.providers.scenarios.premature_harvest",
    "contamination": "agent.providers.scenarios.contamination",
    "slow_growth": "agent.providers.scenarios.slow_growth",
}

_cache: dict[str, Scenario] = {}


def load_scenario(name: str) -> Scenario:
    """Load a scenario by name (cached)."""
    if name in _cache:
        return _cache[name]

    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}")

    import importlib
    module = importlib.import_module(_REGISTRY[name])
    scenario: Scenario = module.SCENARIO
    _cache[name] = scenario
    return scenario


def available_scenarios() -> list[str]:
    return sorted(_REGISTRY.keys())
