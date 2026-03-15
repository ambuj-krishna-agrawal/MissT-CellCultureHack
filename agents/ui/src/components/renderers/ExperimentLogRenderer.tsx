import { motion } from "framer-motion";
import { SectionLabel, Tag } from "./primitives";

function GrowthCurve({ measurements }: { measurements: Array<Record<string, unknown>> }) {
  if (measurements.length < 2) return null;

  const W = 400;
  const H = 120;
  const PAD = 28;

  const points = measurements.map((m) => ({
    time: Number(m.time_min ?? 0),
    count: Number(m.cell_count ?? 0),
  }));

  const maxTime = Math.max(...points.map((p) => p.time), 1);
  const maxCount = Math.max(...points.map((p) => p.count), 1);

  const toX = (t: number) => PAD + ((t / maxTime) * (W - PAD * 2));
  const toY = (c: number) => {
    if (c <= 0) return H - PAD;
    const logC = Math.log10(c);
    const logMax = Math.log10(maxCount);
    const logMin = Math.log10(Math.max(points[0].count, 1));
    const range = logMax - logMin || 1;
    return H - PAD - ((logC - logMin) / range) * (H - PAD * 2);
  };

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${toX(p.time).toFixed(1)} ${toY(p.count).toFixed(1)}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 140 }}>
      <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="#334155" strokeWidth={0.5} />
      <line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD} stroke="#334155" strokeWidth={0.5} />

      <motion.path
        d={pathD}
        fill="none"
        stroke="#34d399"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
      />

      {points.map((p, i) => (
        <motion.circle
          key={i}
          cx={toX(p.time)}
          cy={toY(p.count)}
          r={3.5}
          fill="#34d399"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2 + i * 0.15 }}
        />
      ))}

      <text x={W / 2} y={H - 6} textAnchor="middle" fill="#64748b" fontSize={10}>
        Time (min)
      </text>
      <text x={10} y={H / 2} textAnchor="middle" fill="#64748b" fontSize={10} transform={`rotate(-90, 10, ${H / 2})`}>
        Cells (log)
      </text>

      {points.map((p, i) => (
        <text
          key={`label-${i}`}
          x={toX(p.time)}
          y={toY(p.count) - 10}
          textAnchor="middle"
          fill="#94a3b8"
          fontSize={9}
        >
          {p.time}m
        </text>
      ))}
    </svg>
  );
}

export function ExperimentLogRenderer({ data }: { data: Record<string, unknown> }) {
  const measurements = (data.measurements ?? []) as Array<Record<string, unknown>>;
  const events = (data.events ?? []) as Array<Record<string, unknown>>;
  const organism = String(data.organism ?? "V. natriegens");
  const strain = String(data.strain ?? "");
  const elapsed = Number(data.elapsed_min ?? 0);
  const currentCount = String(data.current_cell_count_display ?? "—");
  const phase = String(data.current_phase ?? "unknown");
  const avgRate = data.average_growth_rate != null ? Number(data.average_growth_rate) : null;

  const PHASE_COLORS: Record<string, string> = {
    lag: "#94a3b8",
    exponential: "#34d399",
    late_exponential: "#fbbf24",
    stationary: "#ef4444",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[15px] font-semibold text-zinc-200">{organism}</div>
          {strain && <div className="text-[14px] text-zinc-500">{strain}</div>}
        </div>
        <div className="text-right">
          <div className="text-[15px] font-bold text-zinc-200 tabular-nums">{currentCount}</div>
          <Tag color={PHASE_COLORS[phase] ?? "#94a3b8"}>{phase.replace(/_/g, " ")}</Tag>
        </div>
      </div>

      <div>
        <SectionLabel>Growth Curve</SectionLabel>
        <div className="rounded-lg bg-white/[0.02] p-3 border border-white/[0.04] mt-1.5">
          <GrowthCurve measurements={measurements} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-white/[0.03] p-3 text-center border border-white/[0.04]">
          <div className="text-[13px] text-zinc-500">ELAPSED</div>
          <div className="text-[15px] font-semibold text-zinc-200 tabular-nums mt-1">{elapsed} min</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] p-3 text-center border border-white/[0.04]">
          <div className="text-[13px] text-zinc-500">CYCLES</div>
          <div className="text-[15px] font-semibold text-zinc-200 tabular-nums mt-1">{measurements.length}</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] p-3 text-center border border-white/[0.04]">
          <div className="text-[13px] text-zinc-500">AVG RATE</div>
          <div className="text-[15px] font-semibold text-zinc-200 tabular-nums mt-1">
            {avgRate != null ? `${avgRate}/min` : "—"}
          </div>
        </div>
      </div>

      {events.length > 0 && (
        <div>
          <SectionLabel>Event Timeline</SectionLabel>
          <div className="space-y-1.5 mt-1.5">
            {events.map((e, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2.5 text-[13px]"
              >
                <span className="text-zinc-600 tabular-nums shrink-0 w-12 text-right">
                  {String(e.time_min ?? "")}m
                </span>
                <span className="w-2 h-2 rounded-full bg-sky-400 mt-1.5 shrink-0" />
                <span className="text-zinc-300">{String(e.event ?? "")}</span>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
