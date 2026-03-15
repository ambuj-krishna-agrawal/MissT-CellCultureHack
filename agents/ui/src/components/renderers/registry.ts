/**
 * Single source of truth for tool configuration.
 * Adding a new tool = one entry here + one renderer file.
 */

import type { FC } from "react";

export interface ToolConfig {
  label: string;
  icon: string;
  accent: string;
  inputSummary: (args: Record<string, unknown>) => string | null;
  Renderer: FC<{ data: Record<string, unknown>; args?: Record<string, unknown> }>;
}

// Renderers
import { ElnoraRenderer } from "./ElnoraRenderer";
import { MediaRenderer } from "./MediaRenderer";
import { CompatibilityRenderer } from "./CompatibilityRenderer";
import { WorldStateRenderer } from "./WorldStateRenderer";
import { CameraRenderer } from "./CameraRenderer";
import { RobotRenderer, StationRenderer } from "./RobotRenderer";
import { RobotActionRenderer } from "./RobotActionRenderer";
import { PipetteRenderer } from "./PipetteRenderer";
import { IncubationRenderer } from "./IncubationRenderer";
import { CultureAnalysisRenderer } from "./CultureAnalysisRenderer";
import { ExperimentLogRenderer } from "./ExperimentLogRenderer";
import { HandlingRenderer } from "./HandlingRenderer";
import { AspirateRenderer, AddRenderer } from "./PipetteOpsRenderer";
import { DecapRenderer, RecapRenderer } from "./CappingRenderer";
import { DisposeRenderer, CollectCellsRenderer } from "./FlaskOpsRenderer";
import { ExecutionPlanRenderer, PhaseLoadRenderer } from "./PlanningRenderer";
import { HumanInputRenderer } from "./HumanInputRenderer";
import { GenericRenderer } from "./GenericRenderer";

const truncate = (s: string, n: number) => (s.length > n ? `${s.slice(0, n)}…` : s);

export const TOOL_REGISTRY: Record<string, ToolConfig> = {
  // ── Phase 1: Experiment Design ────────────────────────────────────────
  consult_elnora: {
    label: "Elnora AI",
    icon: "🧪",
    accent: "#818cf8",
    inputSummary: (a) => {
      const q = String(a.query ?? "");
      return q ? `"${truncate(q, 64)}"` : "Consulting Elnora";
    },
    Renderer: ElnoraRenderer,
  },
  follow_up_elnora: {
    label: "Elnora Follow-up",
    icon: "🔄",
    accent: "#818cf8",
    inputSummary: (a) => {
      const msg = String(a.message ?? "");
      return msg ? `"${truncate(msg, 64)}"` : "Iterating with Elnora";
    },
    Renderer: ElnoraRenderer,
  },
  calculate_media_volumes: {
    label: "Media Volumes",
    icon: "🧮",
    accent: "#34d399",
    inputSummary: (a) => {
      const op = String(a.operation ?? "");
      const lw = String(a.labware ?? "");
      return `${op} — ${lw}`;
    },
    Renderer: MediaRenderer,
  },
  check_compatibility: {
    label: "Compatibility Check",
    icon: "⚗️",
    accent: "#fbbf24",
    inputSummary: (a) => {
      const cell = String(a.cell_line ?? "");
      const lw = String(a.labware ?? "");
      const d = a.density_k_per_cm2;
      return `${cell} + ${lw}${d ? ` @ ${d}k/cm²` : ""}`;
    },
    Renderer: CompatibilityRenderer,
  },

  // ── Planning ────────────────────────────────────────────────────────
  generate_execution_plan: {
    label: "Execution Plan",
    icon: "📋",
    accent: "#818cf8",
    inputSummary: () => "Generating full execution plan",
    Renderer: ExecutionPlanRenderer,
  },
  load_phase_plan: {
    label: "Phase Plan",
    icon: "📂",
    accent: "#34d399",
    inputSummary: (a) => {
      const phase = String(a.phase ?? "");
      return `Loading ${phase.replace(/_/g, " ")}`;
    },
    Renderer: PhaseLoadRenderer,
  },

  // ── Phase 2: Robot Execution ──────────────────────────────────────────
  get_world_state: {
    label: "World State",
    icon: "🌐",
    accent: "#22d3ee",
    inputSummary: () => "Querying workcell state",
    Renderer: WorldStateRenderer,
  },
  get_robot_poses: {
    label: "Robot Poses",
    icon: "🤖",
    accent: "#38bdf8",
    inputSummary: (a) => {
      const c = (a.components as string[]) ?? [];
      return `Querying: ${c.join(", ") || "all"}`;
    },
    Renderer: RobotRenderer,
  },
  get_station_poses: {
    label: "Station Poses",
    icon: "📍",
    accent: "#38bdf8",
    inputSummary: (a) => {
      const s = (a.station_names as string[]) ?? [];
      return s.length ? `Stations: ${s.join(", ")}` : "All stations";
    },
    Renderer: StationRenderer,
  },
  pick_and_place: {
    label: "Pick & Place",
    icon: "🦾",
    accent: "#38bdf8",
    inputSummary: (a) => {
      const obj = String(a.object_id ?? "");
      const from = String(a.from_station ?? "").replace(/_/g, " ");
      const to = String(a.to_station ?? "").replace(/_/g, " ");
      return `${obj}: ${from} → ${to}`;
    },
    Renderer: RobotActionRenderer,
  },
  pipette_transfer: {
    label: "Pipette Transfer",
    icon: "💉",
    accent: "#a78bfa",
    inputSummary: (a) => {
      const transfers = (a.transfers as unknown[]) ?? [];
      const flask = String(a.flask_id ?? "");
      return `${transfers.length} transfers → ${flask}`;
    },
    Renderer: PipetteRenderer,
  },
  set_incubation: {
    label: "Incubation",
    icon: "🌡️",
    accent: "#fb923c",
    inputSummary: (a) => {
      const temp = a.temperature_c;
      const co2 = a.co2_pct;
      return `${temp ?? "37"}°C, ${co2 ?? "5"}% CO₂`;
    },
    Renderer: IncubationRenderer,
  },
  apply_handling: {
    label: "Cell Handling",
    icon: "🤲",
    accent: "#f97316",
    inputSummary: (a) => {
      const mode = String(a.mode ?? "fast");
      const dur = a.duration_seconds;
      return `${mode} — ${dur ?? "?"}s`;
    },
    Renderer: HandlingRenderer,
  },

  pipette_aspirate: {
    label: "Aspirate",
    icon: "⬆️",
    accent: "#ef4444",
    inputSummary: (a) => {
      const reagent = String(a.reagent ?? "");
      const vol = a.volume_mL;
      return `${reagent} · ${vol ?? "?"} mL → waste`;
    },
    Renderer: AspirateRenderer,
  },
  pipette_add: {
    label: "Dispense",
    icon: "⬇️",
    accent: "#22c55e",
    inputSummary: (a) => {
      const reagent = String(a.reagent ?? "");
      const vol = a.volume_mL;
      return `${vol ?? "?"} mL ${reagent}`;
    },
    Renderer: AddRenderer,
  },
  run_decap: {
    label: "Decap",
    icon: "🔓",
    accent: "#f59e0b",
    inputSummary: (a) => `Open ${String(a.flask_id ?? "flask")}`,
    Renderer: DecapRenderer,
  },
  run_recap: {
    label: "Recap",
    icon: "🔒",
    accent: "#22c55e",
    inputSummary: (a) => `Seal ${String(a.flask_id ?? "flask")}`,
    Renderer: RecapRenderer,
  },
  dispose_flask: {
    label: "Dispose Flask",
    icon: "🗑️",
    accent: "#ef4444",
    inputSummary: (a) => {
      const reason = String(a.reason ?? "").replace(/_/g, " ");
      return `${String(a.flask_id ?? "flask")} — ${reason}`;
    },
    Renderer: DisposeRenderer,
  },
  collect_cells: {
    label: "Collect Cells",
    icon: "🧬",
    accent: "#8b5cf6",
    inputSummary: (a) => {
      const vol = a.volume_mL;
      return `${vol ?? "?"} mL → ${String(a.target_container ?? "falcon").replace(/_/g, " ")}`;
    },
    Renderer: CollectCellsRenderer,
  },

  // ── Imaging & Analysis ──────────────────────────────────────────────
  capture_image: {
    label: "Camera Capture",
    icon: "📷",
    accent: "#f472b6",
    inputSummary: (a) => {
      const mode = String(a.mode ?? "visual");
      const cam = String(a.camera_id ?? "zebra_main");
      return `${cam} · ${mode}`;
    },
    Renderer: CameraRenderer,
  },
  analyze_culture: {
    label: "Culture Analysis",
    icon: "🔬",
    accent: "#34d399",
    inputSummary: (a) => {
      const cycle = a.cycle_number;
      const flask = String(a.flask_id ?? "");
      return `Cycle ${cycle ?? "?"} — ${flask}`;
    },
    Renderer: CultureAnalysisRenderer,
  },
  get_experiment_log: {
    label: "Experiment Log",
    icon: "📊",
    accent: "#818cf8",
    inputSummary: (a) => {
      const flask = String(a.flask_id ?? "");
      return flask ? `Flask: ${flask}` : "Fetching log";
    },
    Renderer: ExperimentLogRenderer,
  },

  // ── Cross-phase ───────────────────────────────────────────────────────
  request_human_input: {
    label: "Human Input",
    icon: "👤",
    accent: "#fb923c",
    inputSummary: (a) => {
      const msg = String(a.message ?? a.question ?? "");
      return msg ? truncate(msg.replace(/\*\*/g, "").replace(/\n/g, " "), 60) : "Awaiting input";
    },
    Renderer: HumanInputRenderer,
  },
  sandbox_read: {
    label: "File Read",
    icon: "📂",
    accent: "#94a3b8",
    inputSummary: (a) => (a.path ? String(a.path) : null),
    Renderer: GenericRenderer,
  },
  sandbox_write: {
    label: "File Write",
    icon: "💾",
    accent: "#94a3b8",
    inputSummary: (a) => (a.path ? String(a.path) : null),
    Renderer: GenericRenderer,
  },
};

export const DEFAULT_TOOL_CONFIG: ToolConfig = {
  label: "Tool",
  icon: "⚙️",
  accent: "#94a3b8",
  inputSummary: () => null,
  Renderer: GenericRenderer,
};

export function getToolConfig(toolName: string): ToolConfig {
  return TOOL_REGISTRY[toolName] ?? DEFAULT_TOOL_CONFIG;
}
