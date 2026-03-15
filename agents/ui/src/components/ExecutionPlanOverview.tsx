import { useMemo } from "react";
import { motion } from "framer-motion";
import type { PipelineStep } from "../types";

interface PhaseDefinition {
  id: string;
  name: string;
  shortName: string;
  icon: string;
  color: string;
  toolSignals: string[];
}

const PHASES: PhaseDefinition[] = [
  {
    id: "setup",
    name: "Setup & Configuration",
    shortName: "Setup",
    icon: "⚙️",
    color: "#818cf8",
    toolSignals: ["check_compatibility", "consult_elnora", "generate_execution_plan"],
  },
  {
    id: "monitoring",
    name: "Culture Monitoring & Feeding",
    shortName: "Monitor",
    icon: "🔬",
    color: "#34d399",
    toolSignals: ["get_world_state", "analyze_culture", "pipette_aspirate", "pipette_add", "run_decap", "run_recap"],
  },
  {
    id: "dissociation",
    name: "Dissociation & Delivery",
    shortName: "Harvest",
    icon: "🧬",
    color: "#f59e0b",
    toolSignals: ["collect_cells", "dispose_flask"],
  },
  {
    id: "completion",
    name: "Completion",
    shortName: "Done",
    icon: "✅",
    color: "#22c55e",
    toolSignals: ["complete_experiment"],
  },
];

function detectPhase(step: PipelineStep, stepIndex: number, allSteps: PipelineStep[]): string {
  const tool = step.tool_name;

  if (tool === "complete_experiment" || tool === "get_experiment_log") {
    return "completion";
  }

  if (tool === "collect_cells" || tool === "dispose_flask") {
    return "dissociation";
  }

  if (stepIndex < 6 && (
    tool === "check_compatibility" ||
    tool === "consult_elnora" ||
    tool === "calculate_media_volumes" ||
    tool === "generate_execution_plan" ||
    (tool === "request_human_input" && stepIndex < 6)
  )) {
    return "setup";
  }

  if (tool === "load_phase_plan") {
    const reasoning = step.reasoning?.toLowerCase() ?? "";
    if (reasoning.includes("dissociation") || reasoning.includes("phase 3")) return "dissociation";
    return "monitoring";
  }

  // Use load_phase_plan as a definitive phase boundary:
  // find the last load_phase_plan before this step and inherit its phase
  for (let j = stepIndex - 1; j >= 0; j--) {
    const prev = allSteps[j];
    if (prev.tool_name === "load_phase_plan") {
      const r = prev.reasoning?.toLowerCase() ?? "";
      if (r.includes("dissociation") || r.includes("phase 3")) return "dissociation";
      return "monitoring";
    }
  }

  if (stepIndex >= 4) {
    return "monitoring";
  }

  return "setup";
}

interface PhaseProgress {
  phase: PhaseDefinition;
  status: "pending" | "active" | "completed";
  stepCount: number;
  completedSteps: number;
  cycleNumber?: number;
}

function computePhaseProgress(steps: PipelineStep[], runStatus: string): PhaseProgress[] {
  const phaseSteps: Record<string, PipelineStep[]> = {};
  PHASES.forEach((p) => { phaseSteps[p.id] = []; });

  steps.forEach((step, i) => {
    const phaseId = detectPhase(step, i, steps);
    if (phaseSteps[phaseId]) {
      phaseSteps[phaseId].push(step);
    }
  });

  let seenActive = false;
  return PHASES.map((phase) => {
    const phaseS = phaseSteps[phase.id];
    const completed = phaseS.filter((s) => s.status === "completed").length;
    const hasRunning = phaseS.some((s) => s.status === "running");
    const total = phaseS.length;

    let status: "pending" | "active" | "completed";
    if (hasRunning || (total > 0 && completed < total && completed > 0)) {
      status = "active";
      seenActive = true;
    } else if (total > 0 && completed === total) {
      status = "completed";
    } else if (seenActive || total === 0) {
      status = "pending";
    } else {
      status = "pending";
    }

    if (runStatus === "completed") {
      status = "completed";
    }

    let cycleNumber: number | undefined;
    if (phase.id === "monitoring") {
      const analyzeCalls = phaseS.filter((s) => s.tool_name === "analyze_culture");
      if (analyzeCalls.length > 0) {
        cycleNumber = analyzeCalls.length;
      }
    }

    return {
      phase,
      status,
      stepCount: total,
      completedSteps: completed,
      cycleNumber,
    };
  });
}

interface Props {
  steps: PipelineStep[];
  runStatus: string;
}

export default function ExecutionPlanOverview({ steps, runStatus }: Props) {
  const phases = useMemo(() => computePhaseProgress(steps, runStatus), [steps, runStatus]);

  if (steps.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-4xl px-6 mt-4 mb-0"
    >
      <div className="rounded-xl border border-zinc-800/40 bg-surface-2/60 backdrop-blur-sm px-4 py-3">
        {/* Phase nodes connected by lines */}
        <div className="flex items-center gap-0">
          {phases.map((p, i) => (
            <div key={p.phase.id} className="flex items-center flex-1 last:flex-none">
              {/* Node */}
              <div className="flex flex-col items-center gap-1.5 relative">
                <motion.div
                  className={`
                    relative flex h-9 w-9 items-center justify-center rounded-full text-base
                    transition-all duration-500
                    ${p.status === "completed"
                      ? "bg-emerald-500/15 border-2 border-emerald-500/40"
                      : p.status === "active"
                      ? "border-2"
                      : "bg-zinc-800/40 border-2 border-zinc-700/30"
                    }
                  `}
                  style={p.status === "active" ? {
                    borderColor: `${p.phase.color}60`,
                    backgroundColor: `${p.phase.color}15`,
                  } : undefined}
                >
                  {/* Pulse ring for active */}
                  {p.status === "active" && (
                    <motion.div
                      animate={{ scale: [1, 1.6, 1], opacity: [0.4, 0, 0.4] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute inset-0 rounded-full"
                      style={{ border: `2px solid ${p.phase.color}40` }}
                    />
                  )}

                  {p.status === "completed" ? (
                    <motion.svg
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 15 }}
                      className="h-4 w-4 text-emerald-400"
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </motion.svg>
                  ) : (
                    <span className={p.status === "pending" ? "grayscale opacity-40" : ""}>
                      {p.phase.icon}
                    </span>
                  )}
                </motion.div>

                {/* Label */}
                <div className="flex flex-col items-center">
                  <span className={`
                    text-[11px] font-semibold tracking-wide
                    ${p.status === "completed" ? "text-emerald-400/70"
                      : p.status === "active" ? "text-zinc-200"
                      : "text-zinc-600"}
                  `}>
                    {p.phase.shortName}
                  </span>

                  {/* Step counter or cycle indicator */}
                  {p.stepCount > 0 && (
                    <span className="text-[10px] text-zinc-600 tabular-nums">
                      {p.completedSteps}/{p.stepCount}
                      {p.cycleNumber != null && ` · C${p.cycleNumber}`}
                    </span>
                  )}
                </div>
              </div>

              {/* Connector line */}
              {i < phases.length - 1 && (
                <div className="flex-1 mx-2 h-[2px] relative self-start mt-[18px]">
                  <div className="absolute inset-0 bg-zinc-800/60 rounded-full" />
                  {p.status === "completed" ? (
                    <motion.div
                      className="absolute inset-y-0 left-0 rounded-full bg-emerald-400"
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                    />
                  ) : p.status === "active" ? (
                    <motion.div
                      className="absolute inset-y-0 left-0 rounded-full"
                      style={{ backgroundColor: `${p.phase.color}60`, width: "30%" }}
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    />
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export { PHASES, detectPhase };
export type { PhaseProgress };
