import { useState } from "react";
import { motion } from "framer-motion";
import { Tag, ImageLightbox, ComparisonLightbox } from "./primitives";

interface CaptureEntry {
  day: number;
  confluence_pct: number;
  culture_phase: string;
  image_url: string;
  current?: boolean;
}

function confluenceColor(pct: number): string {
  return pct >= 70 ? "#fbbf24" : pct >= 50 ? "#38bdf8" : "#34d399";
}

function phaseLabel(phase: string): string {
  switch (phase) {
    case "growing": return "Growing";
    case "dissociating": return "Dissociating";
    case "suspended": return "Suspended";
    case "harvested": return "Harvested";
    default: return phase;
  }
}

function phaseTagColor(phase: string): string {
  switch (phase) {
    case "growing": return "#34d399";
    case "dissociating": return "#f97316";
    case "suspended": return "#a78bfa";
    case "harvested": return "#60a5fa";
    default: return "#94a3b8";
  }
}

export function CultureAnalysisRenderer({ data }: { data: Record<string, unknown> }) {
  const confluence = Number(data.confluence_pct ?? 0);
  const protocolDay = data.protocol_day != null ? Number(data.protocol_day) : null;
  const flaskId = String(data.flask_id ?? "—");
  const recommendation = String(data.recommendation ?? "");
  const readyForPassage = Boolean(data.ready_for_passage);
  const needsFeeding = Boolean(data.needs_feeding);
  const cellsInSuspension = Boolean(data.cells_in_suspension);
  const imageUrl = typeof data.image_url === "string" ? data.image_url : null;
  const culturePhase = typeof data.culture_phase === "string" ? data.culture_phase : "growing";

  const captureHistory = Array.isArray(data.capture_history)
    ? (data.capture_history as CaptureEntry[])
    : [];
  const hasHistory = captureHistory.length > 1;

  const morphology = (data.morphology ?? {}) as Record<string, unknown>;
  const viability = (data.viability ?? {}) as Record<string, unknown>;
  const contamination = (data.contamination ?? {}) as Record<string, unknown>;

  const deadPct = Number(viability.dead_cells_pct ?? 0);
  const viabilityPct = (100 - deadPct).toFixed(1);
  const contamDetected = Boolean(contamination.detected);

  const statusColor = readyForPassage ? "#fbbf24" : needsFeeding ? "#38bdf8" : cellsInSuspension ? "#34d399" : "#94a3b8";
  const statusLabel = readyForPassage ? "Ready for Passage" : needsFeeding ? "Needs Feeding" : cellsInSuspension ? "Cells in Suspension" : "Monitoring";

  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
  const [comparisonOpen, setComparisonOpen] = useState(false);

  const comparisonEntries = captureHistory.map((e) => ({
    day: e.day,
    confluence_pct: e.confluence_pct,
    image_url: e.image_url,
    current: e.current,
  }));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="text-[13px] text-zinc-500 uppercase tracking-wider">
          Culture Analysis{protocolDay != null ? ` — Day ${protocolDay}` : ""}
        </div>
        <Tag color={statusColor}>{statusLabel}</Tag>
      </div>

      {/* Capture history — up to 3 entries side by side */}
      {hasHistory ? (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-5 border border-white/[0.06]"
        >
          <div className="flex items-center gap-2 mb-4">
            <svg className="h-3.5 w-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z" />
            </svg>
            <span className="text-[12px] font-medium text-zinc-400 uppercase tracking-wider">
              Capture History
            </span>
          </div>

          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${captureHistory.length}, 1fr)` }}>
            {captureHistory.map((entry, idx) => {
              const isCurrent = Boolean(entry.current);
              const color = confluenceColor(entry.confluence_pct);
              const isPhaseChange = idx > 0 && entry.culture_phase !== captureHistory[idx - 1].culture_phase;
              return (
                <div key={idx} className="relative">
                  {/* Phase change divider */}
                  {isPhaseChange && (
                    <div className="absolute -left-2 top-0 bottom-0 flex items-center">
                      <div className="w-px h-full bg-gradient-to-b from-transparent via-amber-500/40 to-transparent" />
                    </div>
                  )}

                  <div className={`rounded-xl border-2 p-3 transition-all ${
                    isCurrent
                      ? "border-indigo-500/40 bg-indigo-500/[0.06] shadow-[0_0_20px_-6px_rgba(99,102,241,0.2)]"
                      : "border-white/[0.06] bg-white/[0.02]"
                  }`}>
                    {/* Day + Phase label */}
                    <div className="flex items-center justify-between mb-2.5">
                      <span className={`text-[12px] font-bold uppercase tracking-wide ${
                        isCurrent ? "text-indigo-300" : "text-zinc-400"
                      }`}>
                        Day {entry.day}
                      </span>
                      <span
                        className="text-[9px] font-bold uppercase tracking-wider rounded px-1.5 py-0.5"
                        style={{
                          color: phaseTagColor(entry.culture_phase),
                          background: `${phaseTagColor(entry.culture_phase)}20`,
                        }}
                      >
                        {isCurrent ? "Now" : phaseLabel(entry.culture_phase)}
                      </span>
                    </div>

                    {/* Image */}
                    <button
                      type="button"
                      onClick={() => setComparisonOpen(true)}
                      className="w-full aspect-[4/3] rounded-lg overflow-hidden border border-white/[0.08]
                                 hover:border-white/[0.25] transition-all cursor-pointer mb-3 group"
                    >
                      <img
                        src={entry.image_url}
                        alt={`Day ${entry.day} — ${phaseLabel(entry.culture_phase)}`}
                        className="w-full h-full object-cover group-hover:brightness-110 transition-all"
                      />
                    </button>

                    {/* Confluence value */}
                    <div className="text-2xl font-bold tabular-nums" style={{ color }}>
                      {entry.confluence_pct}%
                    </div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                      {entry.culture_phase === "growing"
                        ? "adherent confluence"
                        : entry.culture_phase === "suspended"
                          ? "cells detached"
                          : entry.culture_phase === "dissociating"
                            ? "enzyme active"
                            : "cells collected"}
                    </div>

                    {/* Mini bar */}
                    <div className="mt-2 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(entry.confluence_pct, 100)}%` }}
                        transition={{ duration: 0.8, ease: "easeOut", delay: isCurrent ? 0.2 : 0 }}
                        className="h-full rounded-full"
                        style={{ background: color }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end mt-3 px-1">
            <button
              type="button"
              onClick={() => setComparisonOpen(true)}
              className="text-[11px] text-indigo-400/70 hover:text-indigo-300 transition-colors flex items-center gap-1"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
              </svg>
              Compare full size
            </button>
          </div>
        </motion.div>
      ) : (
        /* Single capture — no history yet */
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
          className="rounded-xl bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-5 border border-white/[0.06]"
        >
          <div className={`flex gap-4 ${imageUrl ? "items-start" : ""}`}>
            {imageUrl && (
              <button
                type="button"
                onClick={() => setLightboxSrc(imageUrl)}
                className="shrink-0 rounded-lg overflow-hidden border border-white/[0.08] hover:border-white/[0.2] transition-colors cursor-pointer"
              >
                <img
                  src={imageUrl}
                  alt={`Microscopy Day ${protocolDay ?? "?"}`}
                  className="w-24 h-24 object-cover hover:brightness-110 transition-all"
                />
              </button>
            )}
            <div className="flex-1 min-w-0">
              <div className="text-4xl font-bold tabular-nums" style={{ color: confluenceColor(confluence) }}>
                {confluence}%
              </div>
              <div className="mt-3 h-2.5 rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(confluence, 100)}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="h-full rounded-full"
                  style={{ background: confluenceColor(confluence) }}
                />
              </div>
              <div className="flex justify-between mt-1.5 text-xs text-zinc-600">
                <span>0%</span>
                <span className="text-amber-500/60">70% passage</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-white/[0.03] p-3.5 border border-white/[0.04]">
          <div className="text-xs text-zinc-500 uppercase tracking-wider">Viability</div>
          <div className="text-[16px] font-semibold text-emerald-400 mt-1">{viabilityPct}%</div>
          <div className="text-[13px] text-zinc-500 mt-0.5">
            {String(viability.floating_cells ?? "minimal")} floating cells
          </div>
        </div>

        <div className="rounded-lg bg-white/[0.03] p-3.5 border border-white/[0.04]">
          <div className="text-xs text-zinc-500 uppercase tracking-wider">Contamination</div>
          <div className={`text-[16px] font-semibold mt-1 ${contamDetected ? "text-red-400" : "text-emerald-400"}`}>
            {contamDetected ? "Detected" : "Clean"}
          </div>
          <div className="text-[13px] text-zinc-500 mt-0.5">
            {String(contamination.notes ?? "No issues")}
          </div>
        </div>

        <div className="rounded-lg bg-white/[0.03] p-3.5 border border-white/[0.04]">
          <div className="text-xs text-zinc-500 uppercase tracking-wider">Colony Quality</div>
          <div className="text-[14px] font-medium text-zinc-200 mt-1 capitalize">
            {String(morphology.colony_quality ?? "n/a").replace(/_/g, " ")}
          </div>
          <div className="text-[13px] text-zinc-500 mt-0.5">
            {String(morphology.colony_edges ?? morphology.cell_shape ?? "")}
          </div>
        </div>

        <div className="rounded-lg bg-white/[0.03] p-3.5 border border-white/[0.04]">
          <div className="text-xs text-zinc-500 uppercase tracking-wider">Flask</div>
          <div className="text-[14px] font-medium text-zinc-200 mt-1 font-mono">{flaskId}</div>
          {morphology.aggregate_size != null && (
            <div className="text-[13px] text-zinc-500 mt-0.5">
              Aggregates: {String(morphology.aggregate_size)}
            </div>
          )}
        </div>
      </div>

      {/* Recommendation */}
      {recommendation && (
        <div className="flex items-center gap-2 rounded-lg bg-white/[0.02] border border-white/[0.04] px-4 py-2.5">
          <span className="text-[14px] text-zinc-400">{recommendation}</span>
        </div>
      )}

      {lightboxSrc && (
        <ImageLightbox
          src={lightboxSrc}
          alt="Microscopy image"
          open={true}
          onClose={() => setLightboxSrc(null)}
        />
      )}

      {hasHistory && (
        <ComparisonLightbox
          entries={comparisonEntries}
          open={comparisonOpen}
          onClose={() => setComparisonOpen(false)}
        />
      )}
    </div>
  );
}
