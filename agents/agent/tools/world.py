"""World state tool — current state of the iPSC workcell."""

from __future__ import annotations

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def get_world_state(ctx: RunContext[AgentDeps]) -> dict:
    """Get the current world state: flask locations, station occupancy, incubator status, and robot readiness.

    Always call this before physical operations to verify station availability
    and flask positions.
    """
    if ctx.deps.mock_mode:
        await ctx.deps.mock_pause()
        return {
            "flasks": {
                "flask_1": {
                    "station": "Incubator_Slot_A",
                    "type": "T75",
                    "cap_state": "vented",
                    "contents": "iPSC-fast culture in Media A",
                    "cell_line": "iPSC-fast",
                    "media": "Media A",
                    "seeded_at": "2026-03-13T08:00:00Z",
                    "last_fed": "2026-03-13T08:00:00Z",
                    "passage_number": 12,
                },
            },
            "stations": {
                "Flask_Storage": {"occupied_by": None, "status": "available"},
                "BSC_1": {"occupied_by": None, "status": "available", "uv_sterilized": True},
                "Incubator_Slot_A": {
                    "occupied_by": "flask_1",
                    "status": "occupied",
                    "temperature_c": 37.0,
                    "co2_pct": 5.0,
                    "humidity_pct": 95.0,
                    "door": "open (demo mode)",
                },
                "Microscope_Stage": {"occupied_by": None, "status": "available"},
                "Capping_Station": {"occupied_by": None, "status": "available"},
                "Feeding_Station": {"occupied_by": None, "status": "available"},
                "Harvest_Station": {"occupied_by": None, "status": "available"},
                "Shaker_Platform": {"occupied_by": None, "status": "available"},
                "Pipette_Station": {"occupied_by": None, "status": "available"},
                "Waste_Bin": {"status": "available", "capacity_remaining_pct": 85},
            },
            "reagents": {
                "media_a_reservoir": {
                    "type": "Media A (iPSC maintenance media)",
                    "volume_mL": 100.0,
                    "sterile": True,
                    "temperature": "room temperature",
                },
                "tryple_bottle": {
                    "type": "TrypLE Express dissociation reagent",
                    "volume_mL": 50.0,
                    "sterile": True,
                },
                "dpbs_bottle": {
                    "type": "D-PBS (without Ca²⁺ and Mg²⁺)",
                    "volume_mL": 50.0,
                    "sterile": True,
                },
                "falcon_50ml": {
                    "type": "50 mL Falcon tube (collection)",
                    "count": 5,
                    "sterile": True,
                },
            },
            "robot": {
                "model": "UR12e",
                "status": "idle",
                "gripper_holding": None,
                "error_state": None,
            },
            "timestamp": "2026-03-14T14:00:00Z",
            "protocol_day": ctx.deps.protocol_day,
        }

    raise NotImplementedError("Live world state requires ROS 2 world model connection.")
