import { motion } from "framer-motion";
import { Tag, SectionLabel } from "./primitives";

export function AspirateRenderer({ data }: { data: Record<string, unknown> }) {
  const flask = String(data.flask_id ?? "");
  const reagent = String(data.reagent ?? "");
  const vol = Number(data.volume_mL ?? 0);
  const ok = Boolean(data.success ?? true);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Aspirate</SectionLabel>
        <Tag color="#ef4444">↑ Remove</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <Row label="Flask" value={flask} />
        <Row label="Reagent" value={reagent} />
        <Row label="Volume" value={`${vol} mL`} />
        <Row label="Destination" value="waste" />
        <Row
          label="Status"
          value={ok ? "✓ Complete" : "✗ Failed"}
          valueClass={ok ? "text-emerald-400" : "text-red-400"}
        />
      </motion.div>
    </div>
  );
}

export function AddRenderer({ data }: { data: Record<string, unknown> }) {
  const flask = String(data.flask_id ?? "");
  const reagent = String(data.reagent ?? "");
  const vol = Number(data.volume_mL ?? 0);
  const source = String(data.source ?? "");
  const ok = Boolean(data.success ?? true);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Dispense</SectionLabel>
        <Tag color="#22c55e">↓ Add</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <Row label="Flask" value={flask} />
        <Row label="Reagent" value={reagent} />
        <Row label="Volume" value={`${vol} mL`} />
        <Row label="Source" value={source.replace(/_/g, " ")} />
        <Row
          label="Status"
          value={ok ? "✓ Complete" : "✗ Failed"}
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
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between text-[14px]">
      <span className="text-zinc-500">{label}</span>
      <span className={valueClass ?? "text-zinc-200"}>{value}</span>
    </div>
  );
}
