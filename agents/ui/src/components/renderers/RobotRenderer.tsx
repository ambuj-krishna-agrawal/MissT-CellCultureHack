import { DataCard, SectionLabel, StatusDot } from "./primitives";

function CoordDisplay({ label, pos }: { label: string; pos: Record<string, number> }) {
  return (
    <div className="flex items-baseline gap-2.5 text-[14px]">
      <span className="text-zinc-600 w-14 shrink-0">{label}</span>
      <div className="flex gap-3 font-mono text-zinc-400">
        {["x", "y", "z"].map((axis) =>
          pos[axis] !== undefined ? (
            <span key={axis}>
              <span className="text-zinc-600">{axis}</span>
              <span className="ml-0.5">{pos[axis].toFixed(3)}</span>
            </span>
          ) : null,
        )}
      </div>
    </div>
  );
}

export function RobotRenderer({ data }: { data: Record<string, unknown> }) {
  const gripper = (data.gripper ?? {}) as Record<string, unknown>;
  const ee = (data.end_effector ?? {}) as Record<string, unknown>;
  const eePos = (ee.position ?? {}) as Record<string, number>;
  const joints = data.joints as Record<string, unknown> | undefined;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Object.keys(eePos).length > 0 && (
        <DataCard accentColor="#38bdf8">
          <SectionLabel>End Effector</SectionLabel>
          <div className="mt-2.5 space-y-1.5">
            <CoordDisplay label="Position" pos={eePos} />
            {ee.frame != null && (
              <div className="text-[13px] text-zinc-600 pl-[4.25rem]">frame: {String(ee.frame)}</div>
            )}
          </div>
        </DataCard>
      )}

      {Object.keys(gripper).length > 0 && (
        <DataCard accentColor={gripper.holding ? "#fbbf24" : "#34d399"}>
          <SectionLabel>Gripper</SectionLabel>
          <div className="mt-2.5 space-y-2">
            <div className="flex items-center gap-2.5 text-[13px]">
              <StatusDot ok={!gripper.holding} />
              <span className="text-zinc-300">
                {gripper.holding ? "Holding object" : "Open"}
              </span>
            </div>
            <div className="flex gap-5 text-[14px] text-zinc-500">
              {gripper.position_mm != null && <span>{String(gripper.position_mm)}mm</span>}
              {(gripper.force_n as number) != null && <span>{String(gripper.force_n)}N</span>}
            </div>
          </div>
        </DataCard>
      )}

      {joints && (
        <DataCard accentColor="#6366f1">
          <SectionLabel>Joint Positions</SectionLabel>
          <div className="mt-2.5 grid grid-cols-2 gap-x-5 gap-y-1">
            {Object.entries(joints)
              .filter(([k]) => k !== "unit")
              .map(([name, val]) => (
                <div key={name} className="flex items-baseline gap-2 text-[14px]">
                  <span className="text-zinc-600 truncate">{name.replace(/_/g, " ")}</span>
                  <span className="font-mono text-zinc-400 ml-auto">
                    {typeof val === "number" ? val.toFixed(4) : String(val)}
                  </span>
                </div>
              ))}
          </div>
          {(joints as Record<string, unknown>).unit != null && (
            <div className="mt-1.5 text-[13px] text-zinc-600">
              unit: {String((joints as Record<string, unknown>).unit)}
            </div>
          )}
        </DataCard>
      )}
    </div>
  );
}

export function StationRenderer({ data }: { data: Record<string, unknown> }) {
  const stations = (data.stations ?? {}) as Record<string, Record<string, unknown>>;

  return (
    <div className="space-y-2.5">
      <SectionLabel>Station Poses</SectionLabel>
      <div className="grid gap-2">
        {Object.entries(stations).map(([name, info]) => {
          const pose = (info.pose ?? {}) as Record<string, number>;
          const hasError = "error" in info;
          return (
            <div
              key={name}
              className="flex items-center gap-3 rounded-lg border border-zinc-800/40 bg-zinc-900/30 px-4 py-2.5"
            >
              <span className="text-[13px] font-medium text-zinc-300 min-w-[9rem] truncate">
                {name.replace(/_/g, " ")}
              </span>
              {hasError ? (
                <span className="text-[14px] text-red-400/70">{String(info.error)}</span>
              ) : (
                <span className="font-mono text-[14px] text-zinc-500">
                  ({pose.x?.toFixed(2)}, {pose.y?.toFixed(2)}, {pose.z?.toFixed(2)})
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
