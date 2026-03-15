import { motion } from "framer-motion";

export function IncubationRenderer({ data }: { data: Record<string, unknown> }) {
  const temp = Number(data.temperature_c ?? 37);
  const actualTemp = Number(data.actual_temperature_c ?? temp);
  const rpm = Number(data.shake_rpm ?? 0);
  const mode = String(data.mode ?? "continuous");
  const flaskId = String(data.flask_id ?? "");
  const started = data.started as boolean;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <motion.span
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300 }}
          className="text-2xl"
        >
          🌡️
        </motion.span>
        <span className="text-[15px] font-semibold text-zinc-200">
          Incubation {started ? "Started" : "Configured"}
        </span>
        {started && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-2.5 py-1 text-[14px] font-medium text-emerald-400 border border-emerald-400/20"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Active
          </motion.span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-white/[0.03] p-4 text-center border border-white/[0.04]">
          <div className="text-[13px] text-zinc-500 mb-1.5">TEMPERATURE</div>
          <div className="text-xl font-bold tabular-nums text-orange-400">{actualTemp}°C</div>
          <div className="text-[13px] text-zinc-600 mt-0.5">target: {temp}°C</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] p-4 text-center border border-white/[0.04]">
          <div className="text-[13px] text-zinc-500 mb-1.5">SHAKING</div>
          <div className="text-xl font-bold tabular-nums text-sky-400">{rpm}</div>
          <div className="text-[13px] text-zinc-600 mt-0.5">RPM</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] p-4 text-center border border-white/[0.04]">
          <div className="text-[13px] text-zinc-500 mb-1.5">MODE</div>
          <div className="text-[15px] font-semibold text-zinc-200 capitalize">{mode}</div>
          <div className="text-[13px] text-zinc-600 mt-0.5">{flaskId}</div>
        </div>
      </div>
    </div>
  );
}
