import { motion } from "framer-motion";
import { Tag, SectionLabel } from "./primitives";

export function DecapRenderer({ data }: { data: Record<string, unknown> }) {
  const flask = String(data.flask_id ?? "");
  const ok = Boolean(data.success ?? true);
  const dur = Number(data.duration_s ?? 0);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Decap</SectionLabel>
        <Tag color="#f59e0b">🔓 Open</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <Row label="Flask" value={flask} />
        <Row label="Cap" value="removed" />
        <Row label="Duration" value={`${dur.toFixed(1)}s`} />
        <Row
          label="Status"
          value={ok ? "✓ Complete" : "✗ Failed"}
          valueClass={ok ? "text-emerald-400" : "text-red-400"}
        />
      </motion.div>
    </div>
  );
}

export function RecapRenderer({ data }: { data: Record<string, unknown> }) {
  const flask = String(data.flask_id ?? "");
  const ok = Boolean(data.success ?? true);
  const dur = Number(data.duration_s ?? 0);
  const capType = String(data.cap_type ?? "vented");

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Recap</SectionLabel>
        <Tag color="#22c55e">🔒 Sealed</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <Row label="Flask" value={flask} />
        <Row label="Cap" value={`sealed (${capType})`} />
        <Row label="Duration" value={`${dur.toFixed(1)}s`} />
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
