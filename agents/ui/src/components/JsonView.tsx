import { useState } from "react";

interface Props {
  data: string | Record<string, unknown> | unknown;
  maxHeight?: string;
  defaultOpen?: boolean;
}

function ValueNode({ value }: { value: unknown }) {
  if (value === null) return <span className="text-zinc-500 italic">null</span>;
  if (value === undefined) return <span className="text-zinc-500 italic">undefined</span>;
  if (typeof value === "boolean")
    return <span className="text-violet-400">{String(value)}</span>;
  if (typeof value === "number")
    return <span className="text-amber-300">{value}</span>;
  if (typeof value === "string") {
    if (value.length > 200) {
      return <CollapsibleString value={value} />;
    }
    return <span className="text-emerald-400">&quot;{value}&quot;</span>;
  }
  return <span className="text-zinc-400">{String(value)}</span>;
}

function CollapsibleString({ value }: { value: string }) {
  const [expanded, setExpanded] = useState(false);
  const display = expanded ? value : value.slice(0, 120) + "…";
  return (
    <span>
      <span className="text-emerald-400">&quot;{display}&quot;</span>
      <button
        onClick={() => setExpanded((p) => !p)}
        className="ml-1 text-[11px] text-blue-400 hover:text-blue-300"
      >
        {expanded ? "less" : `+${value.length - 120}`}
      </button>
    </span>
  );
}

function JsonNode({ keyName, value, depth, defaultOpen }: {
  keyName?: string | number;
  value: unknown;
  depth: number;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen && depth < 3);

  if (value === null || typeof value !== "object") {
    return (
      <div className="flex" style={{ paddingLeft: depth > 0 ? "1.25rem" : 0 }}>
        {keyName != null && (
          <span className="text-blue-400 shrink-0">{typeof keyName === "string" ? `"${keyName}"` : keyName}: </span>
        )}
        <ValueNode value={value} />
      </div>
    );
  }

  const isArray = Array.isArray(value);
  const entries = isArray
    ? (value as unknown[]).map((v, i) => [i, v] as const)
    : Object.entries(value as Record<string, unknown>);
  const opener = isArray ? "[" : "{";
  const closer = isArray ? "]" : "}";

  if (entries.length === 0) {
    return (
      <div className="flex" style={{ paddingLeft: depth > 0 ? "1.25rem" : 0 }}>
        {keyName != null && (
          <span className="text-blue-400 shrink-0">{typeof keyName === "string" ? `"${keyName}"` : keyName}: </span>
        )}
        <span className="text-zinc-500">{opener}{closer}</span>
      </div>
    );
  }

  return (
    <div style={{ paddingLeft: depth > 0 ? "1.25rem" : 0 }}>
      <div className="flex items-center">
        {keyName != null && (
          <span className="text-blue-400 shrink-0">{typeof keyName === "string" ? `"${keyName}"` : keyName}: </span>
        )}
        <button
          onClick={() => setOpen((p) => !p)}
          className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <svg
            className={`h-3 w-3 transition-transform duration-150 ${open ? "rotate-90" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="m9 5 7 7-7 7" />
          </svg>
          <span>{opener}</span>
          {!open && (
            <span className="text-zinc-600 text-xs ml-0.5">
              {entries.length} {isArray ? "item" : "key"}{entries.length !== 1 ? "s" : ""}
            </span>
          )}
          {!open && <span className="text-zinc-400">{closer}</span>}
        </button>
      </div>
      {open && (
        <>
          {entries.map(([k, v]) => (
            <JsonNode
              key={String(k)}
              keyName={k}
              value={v}
              depth={depth + 1}
              defaultOpen={defaultOpen}
            />
          ))}
          <div className="text-zinc-400" style={{ paddingLeft: "0" }}>{closer}</div>
        </>
      )}
    </div>
  );
}

export default function JsonView({ data, maxHeight = "20rem", defaultOpen = true }: Props) {
  let parsed: unknown;
  try {
    parsed = typeof data === "string" ? JSON.parse(data) : data;
  } catch {
    parsed = data;
  }

  if (parsed === null || typeof parsed !== "object") {
    return (
      <pre className="overflow-auto rounded-lg border border-zinc-800/50 bg-[#0a0a12] p-4
                      font-mono text-[13px] leading-relaxed" style={{ maxHeight }}>
        <ValueNode value={parsed} />
      </pre>
    );
  }

  return (
    <div
      className="overflow-auto rounded-lg border border-zinc-800/50 bg-[#0a0a12] p-4
                 font-mono text-[13px] leading-relaxed"
      style={{ maxHeight }}
    >
      <JsonNode value={parsed} depth={0} defaultOpen={defaultOpen} />
    </div>
  );
}
