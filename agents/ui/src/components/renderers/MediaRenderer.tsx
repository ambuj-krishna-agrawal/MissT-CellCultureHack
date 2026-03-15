import { motion } from "framer-motion";
import { Tag, SectionLabel } from "./primitives";

export function MediaRenderer({ data }: { data: Record<string, unknown> }) {
  const operation = String(data.operation ?? "unknown");
  const labware = String(data.labware ?? "T75");
  const numFlasks = Number(data.num_flasks ?? 1);
  const notes = String(data.notes ?? "");
  const mediaType = String(data.media_type ?? "Media A");

  const volumes: Array<{ label: string; value: string; unit: string }> = [];

  if (operation === "feed") {
    volumes.push(
      { label: "Media to remove", value: String(data.media_to_remove_mL ?? 0), unit: "mL" },
      { label: "Fresh media to add", value: String(data.fresh_media_mL ?? 0), unit: "mL" },
    );
  } else if (operation === "dissociation") {
    volumes.push(
      { label: "DPBS wash", value: String(data.dpbs_wash_mL ?? 0), unit: "mL" },
      { label: "TrypLE", value: String(data.tryple_volume_mL ?? 0), unit: "mL" },
      { label: "Neutralization media", value: String(data.neutralization_media_mL ?? 0), unit: "mL" },
    );
  } else if (operation === "reseed") {
    volumes.push(
      { label: "Fresh media", value: String(data.fresh_media_mL ?? 0), unit: "mL" },
    );
  }

  const opColors: Record<string, string> = {
    feed: "#34d399",
    dissociation: "#fbbf24",
    reseed: "#818cf8",
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <SectionLabel>Volume Calculation</SectionLabel>
        <Tag color={opColors[operation] ?? "#94a3b8"}>
          {operation.charAt(0).toUpperCase() + operation.slice(1)}
        </Tag>
      </div>

      <div className="rounded-lg border border-white/[0.06] overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="text-zinc-400 border-b border-white/[0.06] bg-white/[0.02]">
              <th className="text-left py-2.5 px-4 font-medium">Reagent</th>
              <th className="text-right py-2.5 px-4 font-medium">Volume</th>
            </tr>
          </thead>
          <tbody>
            {volumes.map((v, i) => (
              <motion.tr
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="border-b border-white/[0.03] text-zinc-300"
              >
                <td className="py-2.5 px-4">{v.label}</td>
                <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-emerald-400">
                  {v.value} {v.unit}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-[14px] text-zinc-500">
        <span>Labware: <strong className="text-zinc-300">{labware}</strong></span>
        <span>Media: <strong className="text-zinc-300">{mediaType}</strong></span>
        {numFlasks > 1 && <span>Flasks: <strong className="text-zinc-300">{numFlasks}</strong></span>}
      </div>

      {notes && (
        <div className="text-[14px] text-zinc-500 italic">{notes}</div>
      )}

      {data.protocol != null && (
        <div className="rounded-lg bg-amber-500/5 border border-amber-500/15 px-3.5 py-2.5 text-[14px] text-amber-300/70">
          {String(data.protocol)}
        </div>
      )}
    </div>
  );
}
