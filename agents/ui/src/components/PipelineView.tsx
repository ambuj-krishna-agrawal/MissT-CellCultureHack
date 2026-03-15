import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Markdown from "./Markdown";
import type { PipelineStep, RobotEvent, RunState, Segment, HumanInputRequest } from "../types";
import StepCard from "./StepCard";
import HumanInputPrompt from "./HumanInputPrompt";
import ExecutionPlanOverview, { detectPhase, PHASES } from "./ExecutionPlanOverview";
import PhaseStepProgress from "./PhaseStepProgress";
import { getToolConfig } from "./renderers/registry";

const QUIRKY_MESSAGES = [
  "Pipetting thoughts...",
  "Consulting the colonies...",
  "Calibrating intent...",
  "Culturing a response...",
  "Incubating next move...",
  "Analyzing the situation...",
  "Spinning down ideas...",
  "Checking confluency...",
  "Warming up media...",
  "Tapping for insight...",
];

interface Props {
  run: RunState;
  onHumanResponse: (response: string) => void;
  onStop: () => void;
  onResume: () => void;
}

type DisplayItem =
  | { kind: "query"; text: string }
  | { kind: "step"; step: PipelineStep; reasoning: string; thinking: string }
  | { kind: "output"; text: string }
  | { kind: "live_thinking"; text: string }
  | { kind: "human_input"; request: HumanInputRequest };

function buildDisplayItems(segments: Segment[], humanInput: HumanInputRequest | null, runStatus: string): DisplayItem[] {
  const items: DisplayItem[] = [];
  const isTerminal = runStatus === "completed" || runStatus === "stopped" || runStatus === "error" || runStatus === "idle";

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    if (seg.kind === "query") {
      items.push({ kind: "query", text: seg.text });
    } else if (seg.kind === "reasoning") {
      const next = segments[i + 1];
      if (next && next.kind === "step") continue;
      if (next && next.kind === "output") continue;
      if (isTerminal) continue;
      items.push({ kind: "live_thinking", text: seg.text });
    } else if (seg.kind === "thinking") {
      const next = segments[i + 1];
      if (next && (next.kind === "step" || next.kind === "reasoning")) continue;
      if (next && next.kind === "output") continue;
      if (isTerminal) continue;
      items.push({ kind: "live_thinking", text: seg.text });
    } else if (seg.kind === "step") {
      let reasoning = "";
      let thinking = "";
      for (let j = i - 1; j >= 0; j--) {
        const prev = segments[j];
        if (prev.kind === "reasoning") reasoning = prev.text;
        else if (prev.kind === "thinking") thinking = prev.text;
        else break;
      }
      if (!reasoning && seg.step.reasoning) reasoning = seg.step.reasoning;
      if (!thinking && seg.step.thinking) thinking = seg.step.thinking;
      items.push({ kind: "step", step: seg.step, reasoning, thinking });
    } else if (seg.kind === "output") {
      items.push({ kind: "output", text: seg.text });
    }
  }
  if (humanInput && !isTerminal) {
    items.push({ kind: "human_input", request: humanInput });
  }
  return items;
}

const itemVariants = {
  hidden: { opacity: 0, y: 16, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { type: "spring" as const, stiffness: 300, damping: 30 } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
};

function QuirkyProcessing() {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const initial = Math.floor(Math.random() * QUIRKY_MESSAGES.length);
    setIdx(initial);
    const interval = setInterval(() => {
      setIdx((prev) => (prev + 1) % QUIRKY_MESSAGES.length);
    }, 2400);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-3 py-3 px-2"
    >
      <div className="relative flex h-5 w-5 items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
          className="h-4 w-4 rounded-full border-2 border-indigo-400/40 border-t-indigo-400"
        />
      </div>
      <AnimatePresence mode="wait">
        <motion.span
          key={idx}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.25 }}
          className="text-[15px] font-medium text-indigo-300/50 italic"
        >
          {QUIRKY_MESSAGES[idx]}
        </motion.span>
      </AnimatePresence>
    </motion.div>
  );
}

function extractProtocolDay(step: PipelineStep): number | null {
  if (!step.result) return null;
  try {
    const parsed = JSON.parse(step.result);
    if (typeof parsed === "object" && parsed !== null && "protocol_day" in parsed) {
      return typeof parsed.protocol_day === "number" ? parsed.protocol_day : null;
    }
  } catch { /* not JSON */ }
  return null;
}

function CompactStepRow({
  step,
  reasoning,
  thinking,
  isExpanded,
  onToggle,
  showDayTag,
  robotEvents = [],
}: {
  step: PipelineStep;
  reasoning?: string;
  thinking?: string;
  isExpanded: boolean;
  onToggle: () => void;
  showDayTag?: number | null;
  robotEvents?: RobotEvent[];
}) {
  const config = getToolConfig(step.tool_name);
  const isDone = step.status === "completed";

  return (
    <div>
      {/* Compact header row — always clickable */}
      <motion.button
        type="button"
        onClick={onToggle}
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        className={`w-full flex items-center gap-3 py-1.5 px-3 rounded-lg text-[13px]
                   hover:bg-white/[0.04] transition-colors cursor-pointer group
                   ${isExpanded ? "bg-white/[0.03]" : ""}`}
      >
        <span className="text-zinc-600 tabular-nums w-5 text-right text-[11px]">
          {String(step.step_number).padStart(2, "0")}
        </span>

        {isDone ? (
          <svg className="h-3.5 w-3.5 text-emerald-400/60 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
          </svg>
        ) : (
          <div className="h-3.5 w-3.5 rounded-full border border-zinc-700/40 shrink-0" />
        )}

        <span className="text-sm shrink-0">{config.icon}</span>
        <span className={`font-medium ${isDone ? "text-zinc-400" : "text-zinc-200"}`}>
          {config.label}
        </span>

        {config.inputSummary(step.arguments) && (
          <span className="text-zinc-600 truncate flex-1 text-[12px]">
            {config.inputSummary(step.arguments)}
          </span>
        )}

        {robotEvents.length > 0 && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-cyan-500/10 text-cyan-400/60 border border-cyan-500/15 shrink-0">
            🤖 {robotEvents.length}
          </span>
        )}

        {showDayTag != null && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wide bg-indigo-500/15 text-indigo-300 border border-indigo-500/20 shrink-0">
            Day {showDayTag}
          </span>
        )}

        {step.duration_ms != null && (
          <span className="text-zinc-600 tabular-nums text-[11px] shrink-0">
            {(step.duration_ms / 1000).toFixed(1)}s
          </span>
        )}

        <svg
          className={`h-3 w-3 shrink-0 transition-transform duration-200
                      ${isExpanded ? "rotate-180 text-zinc-400" : "text-zinc-600 opacity-0 group-hover:opacity-100"}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
      </motion.button>

      {/* Expanded detail drawer */}
      {isExpanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="ml-8 mt-1 mb-2"
        >
          <StepCard step={step} reasoning={reasoning ?? ""} thinking={thinking ?? ""} onStop={() => {}} robotEvents={robotEvents} />
        </motion.div>
      )}
    </div>
  );
}

interface PhaseGroup {
  phaseId: string;
  phaseName: string;
  phaseIcon: string;
  phaseColor: string;
  items: DisplayItem[];
  steps: PipelineStep[];
}

function groupItemsByPhase(items: DisplayItem[], allSteps: PipelineStep[]): PhaseGroup[] {
  const groups: PhaseGroup[] = [];
  let currentPhaseId = "setup";

  for (const item of items) {
    if (item.kind === "step") {
      const stepIdx = allSteps.findIndex((s) => s.step_id === item.step.step_id);
      currentPhaseId = detectPhase(item.step, stepIdx >= 0 ? stepIdx : 0, allSteps);
    }

    const phase = PHASES.find((p) => p.id === currentPhaseId) ?? PHASES[0];
    const lastGroup = groups[groups.length - 1];

    if (!lastGroup || lastGroup.phaseId !== currentPhaseId) {
      groups.push({
        phaseId: currentPhaseId,
        phaseName: phase.name,
        phaseIcon: phase.icon,
        phaseColor: phase.color,
        items: [item],
        steps: item.kind === "step" ? [item.step] : [],
      });
    } else {
      lastGroup.items.push(item);
      if (item.kind === "step") {
        lastGroup.steps.push(item.step);
      }
    }
  }

  return groups;
}

export default function PipelineView({ run, onHumanResponse, onStop, onResume }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const [hasNew, setHasNew] = useState(false);
  const userScrolledAwayRef = useRef(false);

  const items = useMemo(
    () => buildDisplayItems(run.segments, run.humanInputRequest, run.status),
    [run.segments, run.humanInputRequest, run.status],
  );

  const allSteps = useMemo(
    () => run.segments.filter((s): s is Extract<typeof s, { kind: "step" }> => s.kind === "step").map((s) => s.step),
    [run.segments],
  );

  // Extract protocol_day from every step that has it in its result
  const stepDayMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const step of allSteps) {
      const day = extractProtocolDay(step);
      if (day != null) map.set(step.step_id, day);
    }
    return map;
  }, [allSteps]);

  const phaseGroups = useMemo(
    () => groupItemsByPhase(items, allSteps),
    [items, allSteps],
  );

  // Track which phases the user manually collapsed/expanded (overrides auto)
  // true = user wants collapsed, false = user wants expanded, undefined = use auto
  const [manualCollapsed, setManualCollapsed] = useState<Record<string, boolean>>({});

  // We need a ref so togglePhase can read current auto-collapse state
  const phaseGroupsRef = useRef(phaseGroups);
  phaseGroupsRef.current = phaseGroups;

  const togglePhase = useCallback((phaseId: string) => {
    setManualCollapsed((prev) => {
      if (prev[phaseId] !== undefined) {
        // Already has override → flip it
        return { ...prev, [phaseId]: !prev[phaseId] };
      }
      // First click: compute what auto-collapse would show, then invert
      const groups = phaseGroupsRef.current;
      const group = groups.find((g) => g.phaseId === phaseId);
      if (!group) return prev;
      const allDone = group.steps.length > 0 && group.steps.every((s) => s.status === "completed");
      const groupIdx = groups.findIndex((g) => g.phaseId === phaseId);
      const laterPhaseStarted = groups.slice(groupIdx + 1).some((g) => g.steps.length > 0);
      const autoIsCollapsed = allDone && laterPhaseStarted;
      // Set to opposite of auto
      return { ...prev, [phaseId]: !autoIsCollapsed };
    });
  }, []);

  // Find which phase currently has a running step (the "active" phase)
  const activePhaseId = useMemo(() => {
    for (const g of phaseGroups) {
      if (g.steps.some((s) => s.status === "running")) return g.phaseId;
      if (g.items.some((i) => i.kind === "human_input")) return g.phaseId;
    }
    return null;
  }, [phaseGroups]);

  const getPhaseCollapsed = useCallback((group: PhaseGroup): boolean => {
    // 1. If user manually toggled this phase, respect that
    const manual = manualCollapsed[group.phaseId];
    if (manual !== undefined) return manual;

    // 2. Auto-collapse: completed phases collapse ONLY if a later phase has started
    const allDone = group.steps.length > 0 && group.steps.every((s) => s.status === "completed");
    if (!allDone) return false; // not done → stay expanded

    // Check if any later phase has steps (means a new phase has started)
    const groupIdx = phaseGroups.findIndex((g) => g.phaseId === group.phaseId);
    const laterPhaseStarted = phaseGroups.slice(groupIdx + 1).some((g) => g.steps.length > 0);
    if (laterPhaseStarted) return true; // later phase exists → collapse this one

    return false; // this is the latest phase, even if done → stay expanded
  }, [manualCollapsed, phaseGroups]);

  const showPhaseHeaders = phaseGroups.length > 0 && allSteps.length > 0;

  // Track which compact steps the user expanded (by step_id)
  const [expandedStepIds, setExpandedStepIds] = useState<Set<string>>(new Set());

  const toggleStep = useCallback((stepId: string) => {
    setExpandedStepIds((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) next.delete(stepId);
      else next.add(stepId);
      return next;
    });
  }, []);

  const isRunFinished = run.status === "completed" || run.status === "stopped" || run.status === "error";

  // Find the index of the latest active or most-recent step for auto-collapse logic.
  // When the run is finished, push the index beyond all steps so every step
  // except the very last one collapses (stepsFromLatest >= 3 for all but last).
  const latestStepIndex = useMemo(() => {
    if (isRunFinished) return allSteps.length + 1;
    const running = allSteps.findIndex((s) => s.status === "running");
    if (running >= 0) return running;
    return allSteps.length - 1;
  }, [allSteps, isRunFinished]);

  // ── Auto-scroll logic ──────────────────────────────────────────────
  // wheel-up IMMEDIATELY marks the user as scrolled away (even during
  // a programmatic animation). The only way back is physically reaching
  // the bottom via wheel-down or clicking the "New steps" button.

  const programmaticScrollRef = useRef(false);
  const userScrollingDownRef = useRef(false);
  const scrollDownTimerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const onWheel = (e: WheelEvent) => {
      if (e.deltaY < 0) {
        userScrolledAwayRef.current = true;
        userScrollingDownRef.current = false;
      } else if (e.deltaY > 0) {
        userScrollingDownRef.current = true;
        clearTimeout(scrollDownTimerRef.current);
        scrollDownTimerRef.current = setTimeout(() => {
          userScrollingDownRef.current = false;
        }, 200);
      }
    };

    const onScroll = () => {
      if (programmaticScrollRef.current) return;
      if (!userScrollingDownRef.current) return;
      const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      if (atBottom) {
        userScrolledAwayRef.current = false;
        setHasNew(false);
      }
    };

    el.addEventListener("wheel", onWheel, { passive: true });
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("scroll", onScroll);
      clearTimeout(scrollDownTimerRef.current);
    };
  }, []);

  const prevStepCountRef = useRef(0);
  useEffect(() => {
    const count = allSteps.length;
    if (count > prevStepCountRef.current) {
      if (!userScrolledAwayRef.current) {
        programmaticScrollRef.current = true;
        endRef.current?.scrollIntoView({ behavior: "smooth" });
        setTimeout(() => { programmaticScrollRef.current = false; }, 600);
      } else {
        setHasNew(true);
      }
    }
    prevStepCountRef.current = count;
  }, [allSteps.length]);

  const scrollToBottom = useCallback(() => {
    userScrolledAwayRef.current = false;
    setHasNew(false);
    programmaticScrollRef.current = true;
    endRef.current?.scrollIntoView({ behavior: "smooth" });
    setTimeout(() => { programmaticScrollRef.current = false; }, 600);
  }, []);

  if (run.status === "idle" && run.segments.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="text-center"
        >
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl
                          border border-zinc-800/60 bg-surface-2 text-4xl
                          shadow-[0_0_60px_-12px_rgba(99,102,241,0.15)]">
            🧫
          </div>
          <h2 className="text-xl font-semibold text-zinc-200 mb-2">Cell Culture Agent</h2>
          <p className="text-[15px] text-zinc-500 max-w-sm leading-relaxed">
            Describe a protocol and the agent will plan, verify, and validate each step automatically.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-zinc-800/60
                          bg-surface-2 px-4 py-2.5 text-[14px] text-zinc-500">
            <span className="text-zinc-600">Try:</span>
            <span className="text-zinc-400">Transfer flask_1 from incubator to microscope</span>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="relative flex-1 overflow-y-auto">
      {/* Phase Overview Bar */}
      {showPhaseHeaders && phaseGroups.length > 1 && (
        <ExecutionPlanOverview steps={allSteps} runStatus={run.status} />
      )}

      <div className="mx-auto max-w-4xl space-y-4 px-6 py-6">
        <AnimatePresence mode="popLayout">
          {showPhaseHeaders ? (
            /* ── Phase-grouped rendering ────────────────────── */
            phaseGroups.map((group) => {
              const isCollapsed = getPhaseCollapsed(group);
              const allDone = group.steps.length > 0 && group.steps.every((s) => s.status === "completed");
              const hasActive = group.steps.some((s) => s.status === "running");
              const completedCount = group.steps.filter((s) => s.status === "completed").length;

              return (
                <motion.div
                  key={`phase-${group.phaseId}`}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                >
                  {/* Phase header */}
                  <button
                    type="button"
                    onClick={() => togglePhase(group.phaseId)}
                    className="w-full flex items-center gap-3 py-2.5 px-3 rounded-xl
                               hover:bg-white/[0.02] transition-colors group cursor-pointer"
                  >
                    <motion.div
                      animate={{ rotate: isCollapsed ? -90 : 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-zinc-600"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                      </svg>
                    </motion.div>

                    <span className="text-base">{group.phaseIcon}</span>
                    <span className="text-[14px] font-semibold text-zinc-300 tracking-tight">
                      {group.phaseName}
                    </span>

                    {/* Status badge */}
                    {allDone ? (
                      <span className="ml-auto flex items-center gap-1 text-[11px] text-emerald-400/70 font-medium">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                        </svg>
                        {group.steps.length} steps
                      </span>
                    ) : hasActive ? (
                      <span className="ml-auto text-[11px] font-medium tabular-nums"
                            style={{ color: group.phaseColor }}>
                        {completedCount}/{group.steps.length} steps
                      </span>
                    ) : group.steps.length > 0 ? (
                      <span className="ml-auto text-[11px] text-zinc-600 tabular-nums">
                        {completedCount}/{group.steps.length}
                      </span>
                    ) : null}
                  </button>

                  {/* Collapsed: show progress node bar as summary */}
                  {isCollapsed && group.steps.length > 0 && (
                    <div className="px-3 pb-2">
                      <PhaseStepProgress steps={group.steps} phaseColor={group.phaseColor} />
                    </div>
                  )}

                  {/* Expanded: show all steps */}
                  {!isCollapsed && (
                    <div>
                      {/* Progress bar at top when many steps */}
                      {group.steps.length > 4 && (
                        <div className="px-3 pb-1">
                          <PhaseStepProgress steps={group.steps} phaseColor={group.phaseColor} />
                        </div>
                      )}

                      <div className="space-y-3 pl-4 border-l-2 ml-4 py-2"
                           style={{ borderColor: `${group.phaseColor}20` }}>
                        {group.items.map((item, i) => {
                          const isActiveStep = item.kind === "step" && item.step.status === "running";
                          const stepIdx = item.kind === "step"
                            ? allSteps.findIndex((s) => s.step_id === item.step.step_id)
                            : -1;
                          const stepsFromLatest = latestStepIndex - stepIdx;
                          const useCompact = item.kind === "step" && !isActiveStep &&
                            item.step.status === "completed" && stepsFromLatest >= 1;

                        if (item.kind === "query") {
                          return (
                            <motion.div
                              key={`q-${i}`}
                              variants={itemVariants}
                              initial="hidden"
                              animate="visible"
                              className="rounded-2xl border border-zinc-800/50 glass px-6 py-5"
                            >
                              <p className="text-base leading-relaxed text-zinc-200">{item.text}</p>
                            </motion.div>
                          );
                        }

                        if (item.kind === "step" && useCompact) {
                          const showDay = (group.phaseId === "monitoring" || group.phaseId === "dissociation")
                            ? (stepDayMap.get(item.step.step_id) ?? null)
                            : null;
                          return (
                            <CompactStepRow
                              key={item.step.step_id}
                              step={item.step}
                              reasoning={item.reasoning}
                              thinking={item.thinking}
                              isExpanded={expandedStepIds.has(item.step.step_id)}
                              onToggle={() => toggleStep(item.step.step_id)}
                              showDayTag={showDay}
                              robotEvents={run.robotEvents[item.step.step_id] ?? []}
                            />
                          );
                        }

                        if (item.kind === "step") {
                          const showDay = (group.phaseId === "monitoring" || group.phaseId === "dissociation")
                            ? (stepDayMap.get(item.step.step_id) ?? null)
                            : null;
                          return (
                            <motion.div
                              key={item.step.step_id}
                              variants={itemVariants}
                              initial="hidden"
                              animate="visible"
                            >
                              {showDay != null && (
                                <div className="mb-2 flex items-center gap-2">
                                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide bg-indigo-500/15 text-indigo-300 border border-indigo-500/20">
                                    Day {showDay}
                                  </span>
                                </div>
                              )}
                              <StepCard step={item.step} reasoning={item.reasoning} thinking={item.thinking} onStop={onStop} robotEvents={run.robotEvents[item.step.step_id] ?? []} />
                            </motion.div>
                          );
                        }

                        if (item.kind === "human_input") {
                          return (
                            <motion.div
                              key={`hi-${i}`}
                              variants={itemVariants}
                              initial="hidden"
                              animate="visible"
                            >
                              <HumanInputPrompt request={item.request} onRespond={onHumanResponse} />
                            </motion.div>
                          );
                        }

                        if (item.kind === "live_thinking") {
                          return (
                            <motion.div
                              key={`lt-${i}`}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              className="flex items-start gap-3 rounded-2xl border border-indigo-500/10 glass-subtle px-5 py-4"
                            >
                              <div className="mt-0.5 h-4 w-4 shrink-0">
                                <motion.div
                                  animate={{ rotate: 360 }}
                                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                  className="h-4 w-4 rounded-full border-2 border-indigo-400/50 border-t-transparent"
                                />
                              </div>
                              <Markdown className="text-[15px] leading-relaxed text-indigo-300/50 italic max-h-40 overflow-y-auto">{item.text}</Markdown>
                            </motion.div>
                          );
                        }

                        if (item.kind === "output") {
                          return (
                            <motion.div
                              key={`o-${i}`}
                              variants={itemVariants}
                              initial="hidden"
                              animate="visible"
                              className="rounded-2xl border border-zinc-800/50 glass px-6 py-5"
                            >
                              <div className="flex items-center gap-2.5 mb-3">
                                <div className="h-6 w-6 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                  <svg className="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                                  </svg>
                                </div>
                                <span className="text-[13px] font-semibold uppercase tracking-wider text-zinc-500">Agent Response</span>
                              </div>
                              <Markdown className="text-[15px] leading-[1.75] text-zinc-300 max-h-[32rem] overflow-y-auto">{item.text}</Markdown>
                            </motion.div>
                          );
                        }

                        return null;
                      })}
                    </div>
                  </div>
                  )}
                </motion.div>
              );
            })
          ) : (
            /* ── Flat rendering (no steps yet) ── */
            items.map((item, i) => {
              if (item.kind === "query") {
                return (
                  <motion.div
                    key={`q-${i}`}
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    className="rounded-2xl border border-zinc-800/50 glass px-6 py-5"
                  >
                    <p className="text-base leading-relaxed text-zinc-200">{item.text}</p>
                  </motion.div>
                );
              }

              if (item.kind === "step") {
                return (
                  <motion.div
                    key={item.step.step_id}
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                  >
                    <StepCard step={item.step} reasoning={item.reasoning} thinking={item.thinking} onStop={onStop} robotEvents={run.robotEvents[item.step.step_id] ?? []} />
                  </motion.div>
                );
              }

              if (item.kind === "human_input") {
                return (
                  <motion.div
                    key={`hi-${i}`}
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                  >
                    <HumanInputPrompt request={item.request} onRespond={onHumanResponse} />
                  </motion.div>
                );
              }

              if (item.kind === "live_thinking") {
                return (
                  <motion.div
                    key={`lt-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-start gap-3 rounded-2xl border border-indigo-500/10 glass-subtle px-5 py-4"
                  >
                    <div className="mt-0.5 h-4 w-4 shrink-0">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="h-4 w-4 rounded-full border-2 border-indigo-400/50 border-t-transparent"
                      />
                    </div>
                    <Markdown className="text-[15px] leading-relaxed text-indigo-300/50 italic max-h-40 overflow-y-auto">{item.text}</Markdown>
                  </motion.div>
                );
              }

              if (item.kind === "output") {
                return (
                  <motion.div
                    key={`o-${i}`}
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    className="rounded-2xl border border-zinc-800/50 glass px-6 py-5"
                  >
                    <div className="flex items-center gap-2.5 mb-3">
                      <div className="h-6 w-6 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                        <svg className="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round"
                                d="m4.5 12.75 6 6 9-13.5" />
                        </svg>
                      </div>
                      <span className="text-[13px] font-semibold uppercase tracking-wider text-zinc-500">Agent Response</span>
                    </div>
                    <Markdown className="text-[15px] leading-[1.75] text-zinc-300 max-h-[32rem] overflow-y-auto">{item.text}</Markdown>
                  </motion.div>
                );
              }

              return null;
            })
          )}
        </AnimatePresence>

        {/* Quirky processing indicator */}
        {run.status === "running" && items.length > 0 && !items.some(i => i.kind === "live_thinking") && (
          <QuirkyProcessing />
        )}

        {/* Completed */}
        {run.status === "completed" && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="flex items-center gap-3 rounded-2xl border border-emerald-500/15 glass-subtle px-5 py-4"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 15, delay: 0.1 }}
              className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/10 border border-emerald-500/25"
            >
              <svg className="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            </motion.div>
            <span className="text-[15px] font-medium text-emerald-400/80">
              Completed in {run.duration_ms != null ? `${(run.duration_ms / 1000).toFixed(1)}s` : "—"}
              {" · "}{run.stepCount} step{run.stepCount !== 1 ? "s" : ""}
            </span>
          </motion.div>
        )}

        {/* Stopped with resume */}
        {run.status === "stopped" && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between rounded-2xl border border-amber-500/15 glass-subtle px-5 py-4"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-500/10 border border-amber-500/25">
                <svg className="h-3.5 w-3.5 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              </div>
              <span className="text-[15px] font-medium text-amber-400/80">
                Paused
                {run.duration_ms != null && ` · ${(run.duration_ms / 1000).toFixed(1)}s`}
              </span>
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={onResume}
              className="flex items-center gap-1.5 rounded-lg px-3.5 py-1.5
                         text-[14px] font-semibold text-emerald-400 transition-colors
                         border border-emerald-500/25 bg-emerald-500/8 hover:bg-emerald-500/15"
            >
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                <path d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
              </svg>
              Resume
            </motion.button>
          </motion.div>
        )}

        {/* Error */}
        {run.error && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-red-500/20 glass-subtle px-5 py-4 text-[15px] text-red-400/80"
          >
            <span className="font-semibold">Error:</span> {run.error}
          </motion.div>
        )}

        <div ref={endRef} className="h-4" />
      </div>

      {/* New steps indicator */}
      <AnimatePresence>
        {hasNew && (
          <motion.button
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.2 }}
            onClick={scrollToBottom}
            className="fixed bottom-24 right-8 z-30 flex items-center gap-2 rounded-full
                       border border-indigo-500/25 bg-indigo-500/10 backdrop-blur-md
                       px-4 py-2 text-[13px] font-medium text-indigo-300
                       shadow-[0_4px_20px_-4px_rgba(99,102,241,0.25)]
                       hover:bg-indigo-500/20 transition-colors cursor-pointer"
          >
            <span>New steps</span>
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
            </svg>
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
