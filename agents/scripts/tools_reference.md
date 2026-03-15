# CellPilot — Complete Tool Reference

All tools available to the CellPilot agent. Each tool is an async Python function with `RunContext[AgentDeps]` as the first parameter. PydanticAI auto-generates JSON schemas from type hints and docstrings.

---

## Phase 1: Setup & Configuration

### `check_compatibility`

**File:** `agent/tools/media.py`

Check if a cell line, labware, and seeding density combination is compatible. Validates media, dissociation reagent, density range, and system support.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cell_line` | `str` | — | Cell line name (e.g. `"iPSC-fast"`) |
| `labware` | `str` | — | Labware type (e.g. `"T75"`) |
| `density_k_per_cm2` | `int` | `12` | Seeding density in thousands of cells per cm² |

**Returns:** `compatible` (bool), `cell_line`, `labware`, `media`, `dissociation_reagent`, `handling`, `doubling_time_hrs`, `feeding_schedule_hrs`, `harvest_confluency_pct`, `passage_confluency_pct`, `surface_area_cm2`, `seeding_density_k_per_cm2`, `total_cells_to_seed`, `media_volume_mL`, `time_to_70pct_confluency_days`, `demo_time_hours`, `warnings`, `checks_passed`

---

### `calculate_media_volumes`

**File:** `agent/tools/media.py`

Calculate media and reagent volumes for iPSC culture operations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `labware` | `str` | — | Labware type (e.g. `"T75"`) |
| `operation` | `str` | — | One of `"feed"` (media change), `"dissociation"` (TrypLE), `"reseed"` (new flask) |
| `num_flasks` | `int` | `1` | Number of flasks |

**Returns (feed):** `media_to_remove_mL`, `fresh_media_mL`, `media_type`, `total_media_needed_mL`, `notes`
**Returns (dissociation):** `relesr_volume_mL`, `dpbs_wash_mL`, `neutralization_media_mL`, `reagent`, `protocol`, `notes`
**Returns (reseed):** `fresh_media_mL`, `surface_area_cm2`, `media_type`, `notes`

---

### `consult_elnora`

**File:** `agent/tools/elnora.py`

Consult Elnora AI for protocol expertise and recommendations. Creates a new task in Elnora and returns the AI-generated protocol. Use this for initial protocol questions. For follow-up refinements on the same protocol, use `follow_up_elnora` with the returned `task_id`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Natural language protocol question or request |
| `context` | `str \| None` | `None` | Optional additional context (organism, conditions, constraints) |

**Returns:** `source` ("elnora"), `status`, `task_id`, `protocol_text` (markdown), `message_id`

**Behavior:**
- `mock_mode=True` → returns cached real Elnora response (no API call)
- `mock_mode=False` → calls live Elnora API via CLI, polls for response (up to ~3 min)

---

### `follow_up_elnora`

**File:** `agent/tools/elnora.py`

Send a follow-up message on an existing Elnora task. Use this to iterate on a protocol — e.g. request modifications, add steps, change parameters. The conversation history is preserved so Elnora has full context.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_id` | `str` | — | The `task_id` returned from a previous `consult_elnora` call |
| `message` | `str` | — | Follow-up message or modification request |

**Returns:** `source`, `status`, `task_id`, `protocol_text`

---

### `request_human_input`

**File:** `agent/tools/human.py`

Pause execution and request input from the human operator. Use this when a decision requires human judgment — e.g. protocol approval, parameter selection, or safety-critical confirmations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | — | Markdown-formatted message to display to the operator |
| `input_fields` | `list[dict] \| None` | `None` | Structured input fields (see field types below) |
| `info_blocks` | `list[dict] \| None` | `None` | Info panels to display (title, content, style) |
| `upcoming_actions` | `list[dict] \| None` | `None` | Preview of next actions if approved |

**Supported `input_fields` types:**

| Type | Description | Type-specific keys |
|------|-------------|-------------------|
| `text` | Free-form text input | `placeholder`, `default` |
| `number` | Numeric input with optional range | `min`, `max`, `step`, `unit`, `default` |
| `select` | Single-select from options | `options` [{value, label}], `default` |
| `multi_select` | Multi-select from options | `options` [{value, label}], `defaults` |
| `confirm` | Yes/No toggle | `default`, `confirm_label`, `deny_label` |
| `info` | Read-only markdown display | `content` (no user input collected) |

**Returns:** `response`, `respondent` ("human_operator" or "system"), `auto` (bool), `fields` (dict of field values), `comments`

---

## Phase 2: Culture Monitoring & Feeding

### `get_world_state`

**File:** `agent/tools/world.py`

Get the current world state: flask locations, station occupancy, incubator status, and robot readiness. Always call this before physical operations to verify station availability and flask positions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

**Returns:** `flasks` (dict of flask objects with station, type, cell_line, media, passage_number), `stations` (dict with occupancy and status), `reagents` (dict with volumes and sterility), `robot` (model, status, gripper state), `timestamp`

---

### `get_robot_poses`

**File:** `agent/tools/robot.py`

Query current robot state: joint positions, end-effector pose, gripper status.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `components` | `list[str]` | — | Which components to query. Options: `"joints"`, `"end_effector"`, `"gripper"` |

**Returns:** `robot_model` ("UR12e"), `enclosure` ("IP54"), `joints` (6 joint angles), `end_effector` (position + orientation), `gripper` (position_mm, force, holding), `status`

---

### `get_station_poses`

**File:** `agent/tools/robot.py`

Query poses of workcell stations (incubator, microscope, BSC, etc).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `station_names` | `list[str] \| None` | `None` | Station names to query. Pass empty list or omit for all stations |

**Available stations:** `Flask_Storage`, `Incubator_Slot_A`, `BSC_1`, `Microscope_Stage`, `Pipette_Station`, `Shaker_Platform`

**Returns:** `stations` (dict of station names → pose {frame, position, approach_offset_z})

---

### `pick_and_place`

**File:** `agent/tools/robot.py`

Pick an object from one station and place it at another. The robot will: approach → grip → lift → transfer → lower → release. Verifies gripper grasp before moving.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `object_id` | `str` | — | ID of the object to move (e.g. `"flask_1"`) |
| `from_station` | `str` | — | Source station name |
| `to_station` | `str` | — | Destination station name |

**Returns:** `action`, `object_id`, `from_station`, `to_station`, `success` (bool), `grasp_verified` (bool), `duration_s`, `motion_id`, `message`

---

### `pipette_transfer`

**File:** `agent/tools/robot.py`

Execute one or more liquid transfers using the pipette station. Each transfer specifies a reagent, volume, and source. The robot will aspirate from the source and dispense into the target flask.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transfers` | `list[dict]` | — | List of transfer steps. Each dict has: `reagent` (str), `volume_uL` (float), `source` (str) |
| `flask_id` | `str` | — | Target flask receiving the liquids |

**Returns:** `action`, `flask_id`, `transfers` (list with status), `total_volume_uL`, `transfer_count`, `success` (bool), `message`

---

### `pipette_aspirate`

**File:** `agent/tools/pipette.py`

Aspirate liquid from a flask and discard to waste. Used for removing spent media, DPBS wash, or any liquid before adding fresh reagent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Flask to aspirate from (e.g. `"flask_1"`) |
| `reagent` | `str` | — | What is being removed (e.g. `"spent_media"`, `"DPBS_wash"`) |
| `volume_mL` | `float` | — | Volume to aspirate in millilitres |

**Returns:** `action`, `flask_id`, `reagent`, `volume_mL`, `destination` ("waste"), `success`, `duration_s`, `operation_id`, `message`

---

### `pipette_add`

**File:** `agent/tools/pipette.py`

Dispense reagent into a flask from a source reservoir. Gently dispenses against the flask wall to avoid disturbing the cell monolayer.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Target flask (e.g. `"flask_1"`) |
| `reagent` | `str` | — | Reagent name (e.g. `"Media_A"`, `"TrypLE"`, `"DPBS"`) |
| `volume_mL` | `float` | — | Volume to dispense in millilitres |
| `source` | `str` | — | Source reservoir or bottle ID (e.g. `"media_a_reservoir"`, `"tryple_bottle"`) |

**Returns:** `action`, `flask_id`, `reagent`, `volume_mL`, `source`, `success`, `duration_s`, `operation_id`, `message`

---

### `run_decap`

**File:** `agent/tools/capping.py`

Remove the cap from a flask at the Capping Station. Flask must already be positioned at the Capping Station via `pick_and_place`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Flask to decap (e.g. `"flask_1"`) |

**Returns:** `action`, `flask_id`, `success`, `cap_status` ("removed"), `duration_s`, `operation_id`, `message`

---

### `run_recap`

**File:** `agent/tools/capping.py`

Replace the cap on a flask at the Capping Station. After recapping, the flask is sealed with a vented cap for CO₂ exchange.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Flask to recap (e.g. `"flask_1"`) |

**Returns:** `action`, `flask_id`, `success`, `cap_status` ("sealed"), `cap_type` ("vented"), `duration_s`, `operation_id`, `message`

---

### `dispose_flask`

**File:** `agent/tools/flask_ops.py`

Dispose of a used flask into the biohazard waste bin. Flask should be capped before disposal.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Flask to dispose (e.g. `"flask_1"`) |
| `reason` | `str` | `"experiment_complete"` | Disposal reason: `"experiment_complete"`, `"contamination_detected"`, `"dissociation_declined"` |

**Returns:** `action`, `flask_id`, `reason`, `success`, `destination` ("biohazard_waste"), `duration_s`, `operation_id`, `message`

---

### `collect_cells`

**File:** `agent/tools/flask_ops.py`

Collect cell suspension from flask into a collection vessel. Reports cell count and viability.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Flask containing the cell suspension |
| `target_container` | `str` | `"falcon_50mL"` | Collection vessel |
| `volume_mL` | `float` | `10.0` | Volume to collect in millilitres |

**Returns:** `action`, `flask_id`, `target_container`, `volume_mL`, `success`, `cell_count`, `cell_count_formatted`, `viability_pct`, `efficiency_pct`, `duration_s`, `operation_id`, `message`

---

### `capture_image`

**File:** `agent/tools/perception.py`

Capture an image from the camera system.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `purpose` | `str` | — | What you are looking for (e.g. `"verify flask positions"`, `"cell count monitoring"`) |
| `camera_id` | `str` | `"zebra_main"` | Camera identifier. `"zebra_main"` for bench, `"microscope"` for cell imaging |
| `mode` | `str` | `"visual"` | Capture mode — `"visual"` for bench verification, `"microscopy"` for cell imaging |

**Returns:** `image_id`, `camera_id`, `mode`, `resolution`, `format`, `purpose`, `timestamp`, `status`
- Microscopy mode also returns: `magnification` ("40x"), `illumination` ("brightfield")

---

### `analyze_culture`

**File:** `agent/tools/analysis.py`

Analyze a microscope image for confluence percentage, colony morphology, viability, and contamination status. Call after `capture_image` to get quantitative culture assessment.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_id` | `str` | — | Image ID from a previous `capture_image` call |
| `flask_id` | `str` | — | Flask being monitored |
| `cycle_number` | `int` | — | Monitoring cycle number (1-based) |

**Returns:** `image_id`, `flask_id`, `cycle_number`, `confluence_pct`, `morphology` (colony_quality, colony_edges, colony_packing, differentiated_cells, cell_shape), `viability` (floating_cells, dead_cells_pct, overall), `contamination` (detected, bacterial, fungal, mycoplasma_risk, notes), `ready_for_passage` (bool), `needs_feeding` (bool), `cells_in_suspension` (bool), `recommendation`

**Mock progression:**
- Cycle 1: 45% confluency (needs feeding)
- Cycle 2: 72% confluency (ready for dissociation)
- Cycle 3: 5% (post-dissociation, cells detached)
- Cycle 4: 2% (after handling, nearly all detached)

---

### `set_incubation`

**File:** `agent/tools/incubation.py`

Configure and start incubation for a flask.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | The flask to incubate |
| `temperature_c` | `float` | `37.0` | Target temperature in Celsius (iPSC optimal: 37°C) |
| `co2_pct` | `float` | `5.0` | CO₂ percentage (iPSC optimal: 5%) |
| `duration_minutes` | `int` | `0` | Duration in minutes. `0` = continuous. Use `5–7` for TrypLE dissociation |
| `mode` | `str` | `"continuous"` | `"continuous"` for ongoing culture, `"timed"` for dissociation incubation |

**Returns:** `flask_id`, `status`, `temperature_c`, `actual_temperature_c`, `co2_pct`, `humidity_pct`, `duration_minutes`, `mode`, `incubator_slot`, `started` (bool), `message`

---

## Phase 3: Dissociation & Delivery

### `apply_handling`

**File:** `agent/tools/handling.py`

Apply mechanical handling to detach cells after dissociation reagent incubation. For iPSC passaging with TrypLE: after enzyme incubation, shake/agitate the flask to dislodge detached cells. `"fast"` mode uses firm tapping; `"gentle"` mode uses light rocking.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | The flask to apply handling to |
| `mode` | `str` | `"fast"` | `"fast"` (firm tapping, quicker detachment) or `"gentle"` (light rocking, larger aggregates) |
| `duration_seconds` | `int` | `10` | Duration of mechanical agitation in seconds |

**Returns:** `action`, `flask_id`, `mode`, `duration_seconds`, `method`, `success` (bool), `detachment_estimate`, `aggregate_size_range`, `motion_id`, `message`

---

## Cross-Phase Tools

### `get_experiment_log`

**File:** `agent/tools/analysis.py`

Return the full experiment log: confluence history, image timeline, events. Call this to get accumulated data across all monitoring cycles for a flask.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flask_id` | `str` | — | Flask to query |

**Returns:** `flask_id`, `cell_line`, `media`, `labware`, `total_cycles`, `total_feeds`, `current_confluence_pct`, `current_viability_pct`, `passage_number`, `measurements` (list of cycle readings), `events` (list of event descriptions)

---

### `sandbox_read`

**File:** `agent/tools/sandbox.py`

Read a file from the agent's sandbox working directory.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Relative path within the sandbox directory |

**Returns:** `path`, `exists` (bool), `content` (str or null), `size_bytes`

---

### `sandbox_write`

**File:** `agent/tools/sandbox.py`

Write a file to the agent's sandbox working directory.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Relative path within the sandbox directory |
| `content` | `str` | — | Content to write to the file |

**Returns:** `path`, `written` (bool), `size_bytes`

---

## Summary Table

| # | Tool Name | Phase | Icon | Purpose |
|---|-----------|-------|------|---------|
| 1 | `check_compatibility` | Setup | ⚗️ | Validate cell line + labware + density |
| 2 | `calculate_media_volumes` | Setup | 🧮 | Calculate feed/dissociation/reseed volumes |
| 3 | `consult_elnora` | Setup | 🧪 | Get expert protocol guidance from Elnora AI |
| 4 | `follow_up_elnora` | Setup | 🔄 | Iterate on Elnora protocol (same conversation) |
| 5 | `request_human_input` | Any | 👤 | Pause and collect structured input from scientist |
| 6 | `get_world_state` | Monitoring | 🌐 | Query flask positions, stations, reagents, robot |
| 7 | `get_robot_poses` | Monitoring | 🤖 | Query joint angles, end-effector, gripper |
| 8 | `get_station_poses` | Monitoring | 📍 | Query workcell station poses |
| 9 | `pick_and_place` | Monitoring | 🦾 | Move objects between stations |
| 10 | `pipette_transfer` | Monitoring | 💉 | Aspirate/dispense liquid transfers |
| 11 | `capture_image` | Monitoring | 📷 | Camera capture (bench or microscopy) |
| 12 | `analyze_culture` | Monitoring | 🔬 | Confluence, morphology, viability analysis |
| 13 | `set_incubation` | Monitoring | 🌡️ | Configure incubator (temp, CO₂, duration) |
| 14 | `apply_handling` | Dissociation | 🤲 | Mechanical tapping/rocking for cell detachment |
| 15 | `get_experiment_log` | Any | 📊 | Full experiment history and measurements |
| 16 | `sandbox_read` | Any | 📂 | Read file from sandbox directory |
| 17 | `sandbox_write` | Any | 💾 | Write file to sandbox directory |

**Total: 17 tools**
