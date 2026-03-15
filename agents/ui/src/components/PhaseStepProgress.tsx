import { motion } from "framer-motion";
import type { PipelineStep } from "../types";
import { getToolConfig } from "./renderers/registry";

interface Props {
  steps: PipelineStep[];
  phaseColor: string;
  maxVisible?: number;
}

export default function PhaseStepProgress({ steps, phaseColor, maxVisible = 20 }: Props) {
  if (steps.length === 0) return null;

  const visible = steps.length <= maxVisible ? steps : steps.slice(-maxVisible);
  const hiddenCount = steps.length - visible.length;

  return (
    <div className="flex items-center gap-0 overflow-hidden px-1 py-2">
      {hiddenCount > 0 && (
        <span className="text-[10px] text-zinc-600 mr-1.5 shrink-0 tabular-nums">
          +{hiddenCount}
        </span>
      )}
      {visible.map((step, i) => {
        const config = getToolConfig(step.tool_name);
        const isLast = i === visible.length - 1;
        const isRunning = step.status === "running";
        const isDone = step.status === "completed";

        return (
          <div key={step.step_id} className="flex items-center">
            {/* Node */}
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.03, type: "spring", stiffness: 400, damping: 20 }}
              className="relative group"
            >
              <motion.div
                className={`
                  flex items-center justify-center rounded-full text-[10px]
                  transition-all duration-300 cursor-default
                  ${isRunning
                    ? "h-7 w-7 border-2"
                    : isDone
                    ? "h-5 w-5 border border-emerald-500/30 bg-emerald-500/10"
                    : "h-5 w-5 border border-zinc-700/40 bg-zinc-800/50"
                  }
                `}
                style={isRunning ? {
                  borderColor: `${phaseColor}80`,
                  backgroundColor: `${phaseColor}20`,
                } : undefined}
              >
                {isRunning && (
                  <motion.div
                    animate={{ scale: [1, 1.8, 1], opacity: [0.5, 0, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="absolute inset-0 rounded-full"
                    style={{ border: `1.5px solid ${phaseColor}50` }}
                  />
                )}

                {isDone ? (
                  <svg className="h-2.5 w-2.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                ) : isRunning ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="h-3 w-3 rounded-full border-[1.5px] border-t-transparent"
                    style={{ borderColor: `${phaseColor}80`, borderTopColor: "transparent" }}
                  />
                ) : (
                  <div className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
                )}
              </motion.div>

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 opacity-0 group-hover:opacity-100
                              transition-opacity pointer-events-none z-20">
                <div className="rounded-md bg-zinc-900 border border-zinc-700/50 px-2 py-1 text-[10px] text-zinc-300
                                whitespace-nowrap shadow-lg">
                  <span className="mr-1">{config.icon}</span>
                  {config.label}
                  {step.duration_ms != null && (
                    <span className="text-zinc-500 ml-1">
                      {(step.duration_ms / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>
              </div>
            </motion.div>

            {/* Connector */}
            {!isLast && (
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: i * 0.03 + 0.05, duration: 0.2 }}
                className="h-[1.5px] origin-left"
                style={{
                  width: "8px",
                  backgroundColor: isDone ? "#34d39980" : `${phaseColor}25`,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
