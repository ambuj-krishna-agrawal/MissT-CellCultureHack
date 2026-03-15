import { motion } from "framer-motion";
import { Tag, SectionLabel } from "./primitives";

export function HandlingRenderer({ data }: { data: Record<string, unknown> }) {
  const mode = String(data.mode ?? "fast");
  const flaskId = String(data.flask_id ?? "flask_1");
  const duration = Number(data.duration_seconds ?? 0);
  const success = Boolean(data.success ?? true);
  const method = String(data.method ?? "");
  const detachmentEst = String(data.detachment_estimate ?? "");

  const isFast = mode === "fast";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Mechanical Handling</SectionLabel>
        <Tag color={isFast ? "#f97316" : "#38bdf8"}>
          {isFast ? "⚡ Fast" : "🤲 Gentle"}
        </Tag>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <div className="flex justify-between text-[14px]">
          <span className="text-zinc-500">Flask</span>
          <span className="text-zinc-200 font-mono">{flaskId}</span>
        </div>
        <div className="flex justify-between text-[14px]">
          <span className="text-zinc-500">Duration</span>
          <span className="text-zinc-200 tabular-nums">{duration}s</span>
        </div>
        {method && (
          <div className="flex justify-between text-[14px]">
            <span className="text-zinc-500">Method</span>
            <span className="text-zinc-200">{method}</span>
          </div>
        )}
        {detachmentEst && (
          <div className="flex justify-between text-[14px]">
            <span className="text-zinc-500">Detachment</span>
            <span className="text-zinc-200">{detachmentEst}</span>
          </div>
        )}
        <div className="flex justify-between text-[14px]">
          <span className="text-zinc-500">Status</span>
          <span className={success ? "text-emerald-400" : "text-red-400"}>
            {success ? "✓ Complete" : "✗ Failed"}
          </span>
        </div>
      </motion.div>
    </div>
  );
}
