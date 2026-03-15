import { motion } from "framer-motion";
import { SectionLabel } from "./primitives";

const REAGENT_COLORS: Record<string, string> = {
  defined_media_premix: "#38bdf8",
  media: "#38bdf8",
  cacl: "#f97316",
  inoculum: "#a78bfa",
  bacteria: "#a78bfa",
};

function colorForReagent(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(REAGENT_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return "#94a3b8";
}

export function PipetteRenderer({ data }: { data: Record<string, unknown> }) {
  const transfers = (data.transfers ?? []) as Array<Record<string, unknown>>;
  const flaskId = String(data.flask_id ?? "");
  const totalVol = Number(data.total_volume_uL ?? 0);
  const success = data.success as boolean;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <span className="text-xl">💉</span>
        <span className="text-[15px] font-semibold text-zinc-200">
          Liquid Transfer → {flaskId}
        </span>
        {success && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="ml-auto inline-flex items-center rounded-full bg-emerald-400/10 px-2.5 py-1 text-[14px] font-medium text-emerald-400 border border-emerald-400/20"
          >
            ✓ Dispensed
          </motion.span>
        )}
      </div>

      <div className="space-y-2">
        <SectionLabel>Transfers</SectionLabel>
        {transfers.map((t, i) => {
          const reagent = String(t.reagent ?? "");
          const vol = Number(t.volume_uL ?? 0);
          const source = String(t.source ?? "");
          const color = colorForReagent(reagent);
          const pct = totalVol > 0 ? (vol / totalVol) * 100 : 0;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="flex items-center gap-3 rounded-lg bg-white/[0.03] p-3 border border-white/[0.04]"
            >
              <div
                className="w-1 self-stretch rounded-full"
                style={{ background: color }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-medium text-zinc-200 truncate">{reagent}</div>
                <div className="text-[14px] text-zinc-500">from {source}</div>
              </div>
              <div className="text-right">
                <div className="text-[13px] font-semibold tabular-nums" style={{ color }}>
                  {vol.toFixed(2)} µL
                </div>
                <div className="text-[13px] text-zinc-600 tabular-nums">{pct.toFixed(1)}%</div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="flex items-center gap-3 pt-1">
        <span className="text-[14px] text-zinc-500">Total dispensed:</span>
        <span className="inline-flex items-center rounded-lg bg-violet-400/10 px-3 py-1.5 text-[13px] font-semibold text-violet-400 border border-violet-400/20">
          {totalVol.toFixed(1)} µL
        </span>
      </div>
    </div>
  );
}
