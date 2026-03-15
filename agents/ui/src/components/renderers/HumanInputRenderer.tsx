import Markdown from "../Markdown";
import { Tag } from "./primitives";

interface InputFieldDef {
  id: string;
  type: string;
  label: string;
  options?: Array<{ value: string; label: string }>;
  confirm_label?: string;
  deny_label?: string;
  unit?: string;
}

function formatFieldValue(field: InputFieldDef | undefined, value: unknown): string {
  if (field?.type === "confirm" || typeof value === "boolean") {
    if (field?.confirm_label && value === true) return field.confirm_label;
    if (field?.deny_label && value === false) return field.deny_label;
    return value ? "Yes" : "No";
  }
  if (field?.type === "select" && field.options) {
    const match = field.options.find((o) => String(o.value) === String(value));
    if (match) return match.label;
  }
  if (field?.type === "multi_select" && Array.isArray(value) && field.options) {
    return value
      .map((v) => {
        const match = field.options!.find((o) => String(o.value) === String(v));
        return match ? match.label : String(v);
      })
      .join(", ");
  }
  if (field?.unit) return `${value} ${field.unit}`;
  return String(value ?? "—");
}

export function HumanInputRenderer({ data, args }: { data: Record<string, unknown>; args?: Record<string, unknown> }) {
  const isAuto = Boolean(data.auto);

  const responseRaw = data.response ?? "";
  let parsedResponse: { action?: string; fields?: Record<string, unknown>; comments?: string | null } | null = null;
  try {
    parsedResponse = typeof responseRaw === "string" ? JSON.parse(responseRaw) : null;
  } catch { /* plain text response */ }

  const fields = (parsedResponse?.fields ?? data.fields ?? {}) as Record<string, unknown>;
  const comments = parsedResponse?.comments ?? (data.comments ? String(data.comments) : null);

  const inputFieldDefs = (args?.input_fields ?? []) as InputFieldDef[];
  const originalMessage = args?.message ? String(args.message) : null;

  const hasFields = Object.keys(fields).length > 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <Tag color={isAuto ? "#94a3b8" : "#34d399"}>
          {isAuto ? "Auto-responded" : "✓ Scientist responded"}
        </Tag>
      </div>

      {/* Show original question context */}
      {originalMessage && (
        <div className="rounded-lg bg-zinc-900/40 border border-zinc-800/30 px-4 py-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1.5">Question</div>
          <Markdown className="text-[14px] text-zinc-500 leading-relaxed">{originalMessage}</Markdown>
        </div>
      )}

      {/* Show field values with labels */}
      {hasFields && (
        <div className="rounded-lg bg-emerald-500/4 border border-emerald-500/10 overflow-hidden">
          <div className="px-4 py-2 border-b border-emerald-500/10">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400/60">
              Selections
            </span>
          </div>
          <div className="divide-y divide-white/[0.03]">
            {Object.entries(fields).map(([key, val]) => {
              const fieldDef = inputFieldDefs.find((f) => f.id === key);
              const label = fieldDef?.label ?? key;
              const display = formatFieldValue(fieldDef, val);

              if (val === "" || val === null || val === undefined) return null;
              if (typeof val === "number" && val === 0 && fieldDef?.type === "number") {
                const optionalText = fieldDef?.label?.toLowerCase().includes("leave 0") ? "Not specified (harvest all)" : "0";
                return (
                  <div key={key} className="flex items-baseline gap-3 px-4 py-2.5">
                    <span className="text-[14px] text-zinc-500 min-w-[120px]">{label}</span>
                    <span className="text-[14px] text-zinc-400 italic">{optionalText}</span>
                  </div>
                );
              }

              return (
                <div key={key} className="flex items-baseline gap-3 px-4 py-2.5">
                  <span className="text-[14px] text-zinc-500 min-w-[120px]">{label}</span>
                  <span className="text-[13px] text-zinc-200 font-medium">{display}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Plain text response (non-structured) */}
      {!hasFields && !parsedResponse && responseRaw && (
        <div className="rounded-lg bg-zinc-900/40 border border-zinc-800/30 px-4 py-3">
          <span className="text-[13px] text-zinc-300">{String(responseRaw)}</span>
        </div>
      )}

      {/* Comments */}
      {comments && (
        <div className="rounded-lg bg-zinc-900/40 border border-zinc-800/30 px-4 py-2.5">
          <div className="text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">Note</div>
          <p className="text-[14px] text-zinc-400 leading-relaxed">{comments}</p>
        </div>
      )}
    </div>
  );
}
