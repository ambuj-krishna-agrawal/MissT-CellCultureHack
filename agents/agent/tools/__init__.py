"""All tool functions — imported by the agent definition.

To add a tool: create an async function with RunContext[AgentDeps] first param,
add it here, done. PydanticAI generates JSON schema from type hints + docstring.
"""

from agent.tools.media import calculate_media_volumes, check_compatibility
from agent.tools.robot import get_robot_poses, get_station_poses, pick_and_place, pipette_transfer
from agent.tools.pipette import pipette_aspirate, pipette_add
from agent.tools.capping import run_decap, run_recap
from agent.tools.flask_ops import dispose_flask, collect_cells
from agent.tools.perception import capture_image
from agent.tools.world import get_world_state
from agent.tools.incubation import set_incubation
from agent.tools.handling import apply_handling
from agent.tools.analysis import analyze_culture, get_experiment_log
from agent.tools.elnora import consult_elnora, follow_up_elnora
from agent.tools.planning import generate_execution_plan, load_phase_plan
from agent.tools.sandbox import sandbox_read, sandbox_write
from agent.tools.human import request_human_input

ALL_TOOLS = [
    # Phase 1: Setup & Configuration
    check_compatibility,
    calculate_media_volumes,
    consult_elnora,
    follow_up_elnora,
    request_human_input,

    # Phase 2: Culture Monitoring & Feeding
    get_world_state,
    get_robot_poses,
    get_station_poses,
    pick_and_place,
    pipette_transfer,
    pipette_aspirate,
    pipette_add,
    run_decap,
    run_recap,
    capture_image,
    analyze_culture,
    set_incubation,

    # Phase 3: Dissociation & Delivery
    apply_handling,
    dispose_flask,
    collect_cells,

    # Planning
    generate_execution_plan,
    load_phase_plan,

    # Cross-phase
    get_experiment_log,
    sandbox_read,
    sandbox_write,
]
