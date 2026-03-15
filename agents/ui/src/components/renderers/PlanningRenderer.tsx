import { motion } from "framer-motion";
import { Tag, SectionLabel } from "./primitives";

export function ExecutionPlanRenderer({ data }: { data: Record<string, unknown> }) {
  const ok = Boolean(data.success ?? true);
  const totalPhases = Number(data.total_phases ?? 0);
  const totalSteps = Number(data.total_steps ?? 0);
  const phaseNames = (data.phase_names as string[]) ?? [];
  const schedule = data.schedule as Record<string, unknown> | undefined;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Execution Plan</SectionLabel>
        <Tag color="#818cf8">📋 Generated</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-3"
      >
        <div className="flex items-center gap-2 text-[14px]">
          <span className="text-emerald-400">✓</span>
          <span className="text-zinc-200 font-medium">
            Full execution plan generated
          </span>
        </div>

        <div className="flex flex-wrap gap-x-5 gap-y-1 text-[13px] text-zinc-400">
          <span><span className="text-zinc-200 font-medium">{totalPhases}</span> phases</span>
          <span><span className="text-zinc-200 font-medium">{totalSteps}</span> total steps</span>
          {schedule?.estimated_protocol_duration_days != null && (
            <span>~<span className="text-zinc-200 font-medium">{String(schedule.estimated_protocol_duration_days)}</span> days</span>
          )}
        </div>

        {phaseNames.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {phaseNames.map((name, i) => (
              <span
                key={i}
                className="inline-flex items-center rounded-md px-2 py-0.5 text-[11px]
                           bg-white/[0.04] text-zinc-500 border border-white/[0.04]"
              >
                {name}
              </span>
            ))}
          </div>
        )}

        <div className="flex justify-between text-[13px] pt-1 border-t border-white/5">
          <span className="text-zinc-500">Status</span>
          <span className={ok ? "text-emerald-400" : "text-red-400"}>
            {ok ? "✓ Plan stored in memory" : "✗ Failed"}
          </span>
        </div>
      </motion.div>
    </div>
  );
}

export function PhaseLoadRenderer({ data }: { data: Record<string, unknown> }) {
  const phaseName = String(data.phase_name ?? data.phase ?? "");
  const stepCount = Number(data.step_count ?? 0);
  const steps = (data.steps as Array<{ id: string; what: string; tool: string }>) ?? [];
  const ok = Boolean(data.success ?? true);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Phase Plan Loaded</SectionLabel>
        <Tag color="#34d399">📂 {phaseName}</Tag>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg bg-white/[0.03] p-4 border border-white/[0.04] space-y-2"
      >
        <div className="flex items-center gap-2 text-[14px]">
          <span className="text-emerald-400">✓</span>
          <span className="text-zinc-200 font-medium">
            {stepCount} steps loaded for execution
          </span>
        </div>

        {steps.length > 0 && (
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {steps.map((s, i) => (
              <div key={s.id ?? i} className="flex items-center gap-2 text-[12px]">
                <span className="text-zinc-600 tabular-nums w-8 shrink-0">{s.id ?? `${i + 1}`}</span>
                <span className="text-zinc-400 truncate flex-1">{s.what}</span>
                <span className="text-zinc-600 font-mono text-[10px] shrink-0">{s.tool}</span>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-between text-[13px] pt-1 border-t border-white/5">
          <span className="text-zinc-500">Status</span>
          <span className={ok ? "text-emerald-400" : "text-red-400"}>
            {ok ? "✓ Ready to execute" : "✗ Failed"}
          </span>
        </div>
      </motion.div>
    </div>
  );
}
