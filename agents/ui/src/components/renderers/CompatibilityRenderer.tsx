import { motion } from "framer-motion";
import { SectionLabel, Tag } from "./primitives";

const SEV_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: "rgba(239,68,68,0.08)", text: "#ef4444", border: "rgba(239,68,68,0.2)" },
  high: { bg: "rgba(249,115,22,0.08)", text: "#f97316", border: "rgba(249,115,22,0.2)" },
  medium: { bg: "rgba(234,179,8,0.08)", text: "#eab308", border: "rgba(234,179,8,0.2)" },
};

export function CompatibilityRenderer({ data }: { data: Record<string, unknown> }) {
  const compatible = data.compatible as boolean;
  const warnings = (data.warnings ?? []) as Array<Record<string, unknown>>;
  const passed = (data.checks_passed ?? []) as string[];
  const order = (data.recommended_addition_order ?? []) as string[];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2.5">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
          className="text-2xl"
        >
          {compatible ? "✅" : "⚠️"}
        </motion.div>
        <span className={`text-[15px] font-semibold ${compatible ? "text-emerald-400" : "text-orange-400"}`}>
          {compatible ? "Compatible — safe to proceed" : "Compatibility issues found"}
        </span>
      </div>

      {warnings.length > 0 && (
        <div className="space-y-2.5">
          <SectionLabel>Warnings</SectionLabel>
          {warnings.map((w, i) => {
            const sev = String(w.severity ?? "medium");
            const colors = SEV_COLORS[sev] ?? SEV_COLORS.medium;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="rounded-lg p-3.5 text-[13px] leading-relaxed"
                style={{ background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Tag color={colors.text}>{sev.toUpperCase()}</Tag>
                  {Array.isArray(w.components) &&
                    (w.components as string[]).map((c) => (
                      <span key={c} className="font-mono text-[14px] opacity-80">{c}</span>
                    ))
                  }
                </div>
                <p>{String(w.message ?? "")}</p>
              </motion.div>
            );
          })}
        </div>
      )}

      {passed.length > 0 && (
        <div className="space-y-1.5">
          <SectionLabel>Checks Passed</SectionLabel>
          {passed.map((p, i) => (
            <div key={i} className="text-[13px] text-zinc-400">• {p}</div>
          ))}
        </div>
      )}

      {order.length > 0 && (
        <div className="space-y-2">
          <SectionLabel>Recommended Addition Order</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {order.map((item, i) => (
              <div key={i} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-zinc-600 text-[13px]">→</span>}
                <span
                  className={`inline-flex items-center rounded-md px-2.5 py-1 text-[14px] font-medium ${
                    item.includes("LAST")
                      ? "bg-orange-400/10 text-orange-400 border border-orange-400/20"
                      : "bg-white/5 text-zinc-300 border border-white/10"
                  }`}
                >
                  {item}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
