import { motion } from "framer-motion";

export function RobotActionRenderer({ data }: { data: Record<string, unknown> }) {
  const action = String(data.action ?? "pick_and_place");
  const objectId = String(data.object_id ?? "");
  const from = String(data.from_station ?? "");
  const to = String(data.to_station ?? "");
  const success = data.success as boolean;
  const duration = data.duration_s != null ? Number(data.duration_s) : null;
  const message = String(data.message ?? "");

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <motion.div
          initial={{ rotate: -20, scale: 0.8 }}
          animate={{ rotate: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
          className="text-2xl"
        >
          🤖
        </motion.div>
        <div>
          <div className="text-[15px] font-semibold text-zinc-200 capitalize">
            {action.replace(/_/g, " ")}
          </div>
          <div className="text-[13px] text-zinc-500">{objectId}</div>
        </div>
        {success && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="ml-auto inline-flex items-center rounded-full bg-emerald-400/10 px-2.5 py-1 text-[14px] font-medium text-emerald-400 border border-emerald-400/20"
          >
            ✓ Complete
          </motion.span>
        )}
      </div>

      <div className="flex items-center gap-3 rounded-lg bg-white/[0.03] p-4">
        <div className="flex-1 text-center">
          <div className="text-[13px] text-zinc-500 mb-1.5">FROM</div>
          <div className="text-[13px] font-medium text-zinc-200 bg-white/5 rounded-lg px-3 py-1.5 border border-white/10">
            {from.replace(/_/g, " ")}
          </div>
        </div>

        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 0.15, duration: 0.4 }}
          className="flex items-center gap-1.5 text-sky-400"
        >
          <div className="w-10 h-px bg-sky-400/40" />
          <span className="text-base">→</span>
          <div className="w-10 h-px bg-sky-400/40" />
        </motion.div>

        <div className="flex-1 text-center">
          <div className="text-[13px] text-zinc-500 mb-1.5">TO</div>
          <div className="text-[13px] font-medium text-zinc-200 bg-white/5 rounded-lg px-3 py-1.5 border border-white/10">
            {to.replace(/_/g, " ")}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4 text-[14px] text-zinc-500">
        {duration != null && <span>Duration: {duration.toFixed(1)}s</span>}
        {message && <span className="text-zinc-300">{message}</span>}
      </div>
    </div>
  );
}
