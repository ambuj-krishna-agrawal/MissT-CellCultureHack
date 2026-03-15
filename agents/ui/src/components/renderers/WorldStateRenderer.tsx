import { DataCard, SectionLabel, StatusDot } from "./primitives";

export function WorldStateRenderer({ data }: { data: Record<string, unknown> }) {
  const flasks = (data.flasks ?? {}) as Record<string, Record<string, unknown>>;
  const stations = (data.stations ?? {}) as Record<string, Record<string, unknown>>;
  const robot = (data.robot ?? {}) as Record<string, unknown>;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Object.keys(flasks).length > 0 && (
        <DataCard accentColor="#a78bfa">
          <SectionLabel>Flasks</SectionLabel>
          <div className="mt-2.5 space-y-2.5">
            {Object.entries(flasks).map(([id, info]) => (
              <div key={id} className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <StatusDot ok />
                  <span className="text-[13px] font-semibold text-zinc-200">{id}</span>
                  <span className="text-[13px] text-zinc-600">{String(info.type ?? "")}</span>
                </div>
                <div className="pl-5 text-[14px] text-zinc-500 leading-relaxed">
                  {info.cell_line != null && <span>{String(info.cell_line)} P{String(info.passage ?? "?")}</span>}
                  {info.station != null && <span> · {String(info.station).replace(/_/g, " ")}</span>}
                  {info.media_type != null && <div className="text-zinc-600">{String(info.media_type)}</div>}
                </div>
              </div>
            ))}
          </div>
        </DataCard>
      )}

      {Object.entries(stations).length > 0 && (
        <DataCard accentColor="#22d3ee">
          <SectionLabel>Stations</SectionLabel>
          <div className="mt-2.5 space-y-2">
            {Object.entries(stations).map(([id, info]) => {
              const occupied = info.occupied_by != null;
              return (
                <div key={id} className="flex items-center gap-2.5 text-[13px]">
                  <StatusDot ok={!occupied} />
                  <span className="text-zinc-300 min-w-0 truncate">{id.replace(/_/g, " ")}</span>
                  {occupied ? (
                    <span className="ml-auto text-[14px] text-violet-400/70 shrink-0">
                      {String(info.occupied_by)}
                    </span>
                  ) : (
                    <span className="ml-auto text-[14px] text-emerald-500/50 shrink-0">open</span>
                  )}
                  {info.temperature_c != null && (
                    <span className="text-[13px] text-zinc-600 shrink-0">
                      {String(info.temperature_c)}°C
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </DataCard>
      )}

      {robot.status != null && (
        <DataCard accentColor="#38bdf8">
          <SectionLabel>Robot</SectionLabel>
          <div className="mt-2.5 flex items-center gap-2.5 text-[13px]">
            <StatusDot ok={robot.status === "idle"} />
            <span className="text-zinc-300 capitalize">{String(robot.status)}</span>
            {robot.gripper_holding != null && (
              <span className="text-[14px] text-amber-400/70">
                holding {String(robot.gripper_holding)}
              </span>
            )}
            {robot.error_state != null && (
              <span className="text-[14px] text-red-400/70">{String(robot.error_state)}</span>
            )}
          </div>
        </DataCard>
      )}
    </div>
  );
}
