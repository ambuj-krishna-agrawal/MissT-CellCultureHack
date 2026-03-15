import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Markdown from "./Markdown";
import type { PipelineStep, RobotEvent } from "../types";
import { getToolConfig } from "./renderers/registry";
import ToolResultView from "./ToolResultView";
import JsonView from "./JsonView";

interface Props {
  step: PipelineStep;
  reasoning: string;
  thinking: string;
  onStop?: () => void;
  robotEvents?: RobotEvent[];
}

export default function StepCard({ step, reasoning, thinking, onStop, robotEvents = [] }: Props) {
  const [showRaw, setShowRaw] = useState(false);
  const [showThinking, setShowThinking] = useState(false);
  const config = getToolConfig(step.tool_name);
  const isRunning = step.status === "running";
  const isDone = step.status === "completed";
  const isError = step.status === "error";
  const summary = step.arguments ? config.inputSummary(step.arguments) : null;

  return (
    <motion.div
      layout
      className="relative rounded-2xl border overflow-hidden transition-colors duration-500"
      style={{
        borderColor: isRunning ? `${config.accent}33` : isError ? "rgba(239,68,68,0.2)" : "var(--border)",
        background: isRunning
          ? `linear-gradient(135deg, ${config.accent}08 0%, transparent 60%)`
          : "var(--surface)",
        boxShadow: isRunning ? `0 0 30px -8px ${config.accent}25` : "none",
      }}
    >
      {/* Active shimmer bar */}
      {isRunning && (
        <div className="absolute top-0 left-0 right-0 h-[2px] overflow-hidden">
          <div className="h-full w-1/3 animate-shimmer rounded-full"
               style={{ background: `linear-gradient(90deg, transparent, ${config.accent}80, transparent)` }} />
        </div>
      )}

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-3.5 px-5 py-4">
        {/* Step number + status icon */}
        <div className="relative flex-shrink-0">
          {isRunning && (
            <motion.div
              className="absolute inset-0 rounded-xl animate-ring-pulse"
              style={{ border: `1px solid ${config.accent}40` }}
            />
          )}
          <div
            className="relative flex h-10 w-10 items-center justify-center rounded-xl"
            style={{
              background: isRunning ? `${config.accent}15`
                : isDone ? "rgba(52,211,153,0.08)"
                : "rgba(239,68,68,0.08)",
              border: `1px solid ${
                isRunning ? `${config.accent}30`
                : isDone ? "rgba(52,211,153,0.2)"
                : "rgba(239,68,68,0.2)"
              }`,
            }}
          >
            {isRunning ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="h-4 w-4 rounded-full border-2 border-t-transparent"
                style={{ borderColor: `${config.accent}80`, borderTopColor: "transparent" }}
              />
            ) : isDone ? (
              <motion.svg
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 15 }}
                className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </motion.svg>
            ) : (
              <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            )}
          </div>
        </div>

        {/* Tool info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5">
            <span className="text-[13px] font-mono text-zinc-600 tabular-nums">
              {String(step.step_number).padStart(2, "0")}
            </span>
            <span className="text-lg">{config.icon}</span>
            <span className="text-base font-semibold text-zinc-200">{config.label}</span>
          </div>
          {summary && (
            <p className="mt-1 text-[14px] text-zinc-500 truncate">{summary}</p>
          )}
        </div>

        {/* Duration & controls */}
        <div className="flex items-center gap-3 shrink-0">
          {step.duration_ms != null && (
            <span className="font-mono text-[13px] text-zinc-600">{step.duration_ms.toFixed(0)}ms</span>
          )}
          {isRunning && onStop && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onStop}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5
                         text-[13px] font-semibold text-red-400 transition-colors
                         border border-red-500/20 bg-red-500/8 hover:bg-red-500/15"
            >
              <svg className="h-2.5 w-2.5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              Stop
            </motion.button>
          )}
        </div>
      </div>

      {/* ── Robot Live Events ──────────────────────────────────── */}
      {robotEvents.length > 0 && (
        <div className="border-t border-white/[0.04] px-5 py-3">
          <div className="flex items-center gap-2 mb-2.5">
            <span className="text-[13px]">🤖</span>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400/60">
              Robot Live
            </span>
            <span className="text-[10px] text-zinc-700 ml-auto tabular-nums">
              {robotEvents.length} events
            </span>
          </div>
          <div className="space-y-0.5">
            {robotEvents.map((evt, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.15, delay: i * 0.02 }}
                className="flex items-center gap-2 text-[12px] py-0.5"
              >
                <span className="text-cyan-500/30 text-[10px] tabular-nums w-4 text-right shrink-0">
                  {evt.robot_step}
                </span>
                <span className="text-cyan-400/25">→</span>
                <span className="text-zinc-500">{evt.message}</span>
              </motion.div>
            ))}
            {isRunning && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.3, 0.7, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="flex items-center gap-2 text-[12px] py-0.5 mt-1"
              >
                <div className="w-4" />
                <span className="text-cyan-400/25">→</span>
                <span className="text-cyan-400/30 italic">waiting for robot...</span>
              </motion.div>
            )}
          </div>
        </div>
      )}

      {/* ── Thinking (Claude) ──────────────────────────────────── */}
      <AnimatePresence>
        {thinking && (
          <div className="border-t border-white/[0.03]">
            <button
              onClick={() => setShowThinking((p) => !p)}
              className="flex w-full items-center gap-2 px-5 py-2.5 text-left transition-colors hover:bg-white/[0.02]"
            >
              <span className="text-[13px]">💭</span>
              <span className="text-[13px] font-medium text-orange-400/60 uppercase tracking-wider">
                Thinking
              </span>
              <span className="text-xs text-zinc-700 ml-auto">{thinking.length} chars</span>
            </button>
            <AnimatePresence>
              {showThinking && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="max-h-60 overflow-y-auto border-t border-white/[0.03] px-5 py-3">
                    <p className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-orange-300/40">{thinking}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </AnimatePresence>

      {/* ── Reasoning ──────────────────────────────────────────── */}
      {reasoning && (
        <div className="border-t border-white/[0.04] px-5 py-3.5">
          <Markdown className="text-[15px] leading-[1.7] text-zinc-400">{reasoning}</Markdown>
        </div>
      )}

      {/* ── Tool-specific result ───────────────────────────────── */}
      <AnimatePresence>
        {isDone && step.result != null && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="overflow-hidden border-t border-white/[0.04]"
          >
            <div className="px-5 py-4">
              <ToolResultView toolName={step.tool_name} result={step.result} args={step.arguments} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Raw JSON toggle ────────────────────────────────────── */}
      {isDone && (
        <div className="border-t border-white/[0.03]">
          <button
            onClick={() => setShowRaw((p) => !p)}
            className="flex items-center gap-1.5 px-5 py-2 text-xs text-zinc-700/60
                       hover:text-zinc-500 transition-colors"
          >
            <motion.svg
              animate={{ rotate: showRaw ? 90 : 0 }}
              transition={{ duration: 0.15 }}
              className="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m9 5 7 7-7 7" />
            </motion.svg>
            raw
          </button>
          <AnimatePresence>
            {showRaw && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden border-t border-white/[0.03]"
              >
                <div className="px-5 py-4 space-y-3">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-zinc-700/60 block mb-1.5">Input</span>
                    <JsonView data={step.arguments} maxHeight="14rem" defaultOpen={false} />
                  </div>
                  {step.result != null && (
                    <div>
                      <span className="text-xs uppercase tracking-wider text-zinc-700/60 block mb-1.5">Output</span>
                      <JsonView data={step.result} maxHeight="16rem" defaultOpen={false} />
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}
