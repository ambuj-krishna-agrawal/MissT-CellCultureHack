import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function ImageLightbox({
  src,
  alt,
  open,
  onClose,
}: {
  src: string;
  alt: string;
  open: boolean;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm cursor-pointer"
          onClick={onClose}
        >
          <motion.img
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.85, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            src={src}
            alt={alt}
            className="max-w-[90vw] max-h-[85vh] rounded-xl border border-white/10 shadow-2xl object-contain"
            onClick={(e) => e.stopPropagation()}
          />
          <button
            onClick={onClose}
            className="absolute top-6 right-6 flex h-10 w-10 items-center justify-center rounded-full
                       bg-white/10 border border-white/15 text-white/70 hover:bg-white/20 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export interface ComparisonEntry {
  day: number;
  confluence_pct: number;
  image_url: string;
  current?: boolean;
}

export function ComparisonLightbox({
  entries,
  open,
  onClose,
}: {
  entries: ComparisonEntry[];
  open: boolean;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const confColor = (pct: number) =>
    pct >= 70 ? "#fbbf24" : pct >= 50 ? "#38bdf8" : "#34d399";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/85 backdrop-blur-md cursor-pointer"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="flex gap-6 items-end px-8"
            onClick={(e) => e.stopPropagation()}
          >
            {entries.map((entry) => {
              const isCurrent = Boolean(entry.current);
              const color = confColor(entry.confluence_pct);
              return (
                <div key={entry.day} className="flex flex-col items-center gap-3">
                  {/* Day label */}
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${isCurrent ? "text-indigo-300" : "text-zinc-400"}`}>
                      Day {entry.day}
                    </span>
                    {isCurrent && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/20 px-2 py-0.5 rounded">
                        Current
                      </span>
                    )}
                  </div>

                  {/* Large image */}
                  <div className={`rounded-xl overflow-hidden border-2 shadow-2xl ${
                    isCurrent ? "border-indigo-500/50" : "border-white/10"
                  }`}>
                    <img
                      src={entry.image_url}
                      alt={`Day ${entry.day}`}
                      className="w-[28vw] max-w-[360px] h-[28vw] max-h-[360px] object-cover"
                    />
                  </div>

                  {/* Confluence */}
                  <div className="text-center">
                    <div className="text-2xl font-bold tabular-nums" style={{ color }}>
                      {entry.confluence_pct}%
                    </div>
                    <div className="w-32 mt-1.5 h-1.5 rounded-full bg-white/10 overflow-hidden mx-auto">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(entry.confluence_pct, 100)}%` }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="h-full rounded-full"
                        style={{ background: color }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </motion.div>

          {/* Growth summary */}
          {entries.length >= 2 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2
                         bg-white/[0.08] border border-white/10 rounded-full px-5 py-2"
            >
              <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2 17l6-6 4 4 8-10" />
              </svg>
              <span className="text-[13px] text-zinc-300">
                {entries[0].confluence_pct}% → {entries[entries.length - 1].confluence_pct}%
                {" · "}+{(entries[entries.length - 1].confluence_pct - entries[0].confluence_pct).toFixed(0)}% over {entries.length - 1} day{entries.length > 2 ? "s" : ""}
              </span>
            </motion.div>
          )}

          <button
            onClick={onClose}
            className="absolute top-6 right-6 flex h-10 w-10 items-center justify-center rounded-full
                       bg-white/10 border border-white/15 text-white/70 hover:bg-white/20 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function Tag({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[13px] font-medium leading-none"
      style={{ background: `${color}14`, color, border: `1px solid ${color}22` }}
    >
      {children}
    </span>
  );
}

export function StatusDot({ ok, pulse }: { ok: boolean; pulse?: boolean }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${ok ? "bg-emerald-400" : "bg-zinc-600"}
                  ${pulse ? "animate-pulse" : ""}`}
    />
  );
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs font-bold uppercase tracking-[0.1em] text-zinc-500">
      {children}
    </span>
  );
}

export function MiniTable({ rows }: { rows: Array<{ label: string; value: string; ok?: boolean; accent?: string }> }) {
  return (
    <div className="space-y-1.5">
      {rows.map((r, i) => (
        <div key={i} className="flex items-center gap-3 text-[14px]">
          <span className="text-zinc-500 min-w-[6rem] shrink-0">{r.label}</span>
          <div className="flex items-center gap-2 text-zinc-300">
            {r.ok !== undefined && <StatusDot ok={r.ok} />}
            <span style={r.accent ? { color: r.accent } : undefined}>{r.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export function ConfidenceBar({ value, label, sublabel }: { value: number; label: string; sublabel?: string }) {
  const pct = Math.round(value * 100);
  const color = pct > 90 ? "#34d399" : pct > 70 ? "#fbbf24" : "#f87171";
  return (
    <div className="flex items-center gap-3">
      <div className="min-w-[7rem] shrink-0">
        <span className="text-[14px] text-zinc-300 block leading-tight">{label}</span>
        {sublabel && <span className="text-[13px] text-zinc-600 block">{sublabel}</span>}
      </div>
      <div className="flex-1 h-2 rounded-full bg-zinc-800/80 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="h-full rounded-full"
          style={{ background: color }}
        />
      </div>
      <span
        className="text-[13px] font-mono font-medium w-12 text-right"
        style={{ color }}
      >
        {pct}%
      </span>
    </div>
  );
}

export function DataCard({ children, accentColor }: { children: React.ReactNode; accentColor?: string }) {
  return (
    <div
      className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-4"
      style={accentColor ? { borderLeftColor: `${accentColor}40`, borderLeftWidth: 2 } : undefined}
    >
      {children}
    </div>
  );
}
