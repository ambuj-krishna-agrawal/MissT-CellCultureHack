import { motion } from "framer-motion";
import { Tag, SectionLabel } from "./primitives";

export function DisposeRenderer({ data }: { data: Record<string, unknown> }) {
  const flask = String(data.flask_id ?? "");
  const reason = String(data.reason ?? "").replace(/_/g, " ");
  const ok = Boolean(data.success ?? true);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Dispose Flask</SectionLabel>
        <Tag color="#ef4444">🗑️ Waste</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <Row label="Flask" value={flask} />
        <Row label="Reason" value={reason} />
        <Row label="Destination" value="biohazard waste" />
        <Row
          label="Status"
          value={ok ? "✓ Disposed" : "✗ Failed"}
          valueClass={ok ? "text-emerald-400" : "text-red-400"}
        />
      </motion.div>
    </div>
  );
}

export function CollectCellsRenderer({ data }: { data: Record<string, unknown> }) {
  const flask = String(data.flask_id ?? "");
  const container = String(data.target_container ?? "falcon_50mL").replace(/_/g, " ");
  const vol = Number(data.volume_mL ?? 0);
  const cellCount = String(data.cell_count_formatted ?? "—");
  const viability = Number(data.viability_pct ?? 0);
  const efficiency = Number(data.efficiency_pct ?? 0);
  const ok = Boolean(data.success ?? true);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Cell Collection</SectionLabel>
        <Tag color="#8b5cf6">🧬 Harvest</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <Row label="Flask" value={flask} />
        <Row label="Container" value={container} />
        <Row label="Volume" value={`${vol} mL`} />
        <div className="h-px bg-white/5 my-1" />
        <Row label="Cell Count" value={cellCount} highlight />
        <Row label="Viability" value={`${viability}%`} highlight />
        <Row label="Efficiency" value={`${efficiency}%`} />
        <Row
          label="Status"
          value={ok ? "✓ Collected" : "✗ Failed"}
          valueClass={ok ? "text-emerald-400" : "text-red-400"}
        />
      </motion.div>
    </div>
  );
}

function Row({
  label,
  value,
  valueClass,
  highlight,
}: {
  label: string;
  value: string;
  valueClass?: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between text-[14px]">
      <span className="text-zinc-500">{label}</span>
      <span className={valueClass ?? (highlight ? "text-white font-medium" : "text-zinc-200")}>
        {value}
      </span>
    </div>
  );
}
