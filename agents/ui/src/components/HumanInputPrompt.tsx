import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Markdown from "./Markdown";
import type { HumanInputRequest, InputField } from "../types";

interface Props {
  request: HumanInputRequest;
  onRespond: (response: string) => void;
}

const INFO_STYLES: Record<string, { border: string; bg: string; icon: string; title: string }> = {
  default: { border: "border-zinc-700/40", bg: "bg-zinc-800/30", icon: "📋", title: "text-zinc-300" },
  info: { border: "border-blue-500/20", bg: "bg-blue-500/6", icon: "ℹ️", title: "text-blue-300" },
  warning: { border: "border-amber-500/20", bg: "bg-amber-500/6", icon: "⚠️", title: "text-amber-300" },
  success: { border: "border-emerald-500/20", bg: "bg-emerald-500/6", icon: "✅", title: "text-emerald-300" },
};

function FieldText({ field, value, onChange }: { field: InputField; value: string; onChange: (v: string) => void }) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder ?? ""}
      className="w-full rounded-lg border border-zinc-700/50 bg-zinc-900/60 px-3.5 py-2.5
                 text-[15px] text-zinc-200 placeholder-zinc-600 outline-none
                 focus:border-indigo-500/40 transition-colors"
    />
  );
}

function FieldNumber({ field, value, onChange }: { field: InputField; value: number | string; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={field.min}
        max={field.max}
        step={field.step ?? 1}
        className="flex-1 rounded-lg border border-zinc-700/50 bg-zinc-900/60 px-3.5 py-2.5
                   text-[15px] text-zinc-200 outline-none font-mono
                   focus:border-indigo-500/40 transition-colors"
      />
      {field.unit && (
        <span className="text-[14px] text-zinc-500 font-medium whitespace-nowrap">{field.unit}</span>
      )}
    </div>
  );
}

function FieldSelect({ field, value, onChange }: { field: InputField; value: string; onChange: (v: string) => void }) {
  const options = field.options ?? [];
  return (
    <div className="space-y-1.5">
      {options.map((opt) => (
        <button
          type="button"
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`flex items-center gap-3 rounded-lg border px-3.5 py-3 cursor-pointer transition-all w-full text-left
            ${value === opt.value
              ? "border-indigo-500/40 bg-indigo-500/8"
              : "border-zinc-700/40 bg-zinc-900/30 hover:border-zinc-600/60"
            }`}
        >
          <div className={`h-4 w-4 rounded-full border-2 flex items-center justify-center flex-shrink-0
            ${value === opt.value ? "border-indigo-400" : "border-zinc-600"}`}>
            {value === opt.value && (
              <div className="h-2 w-2 rounded-full bg-indigo-400" />
            )}
          </div>
          <span className={`text-[15px] ${value === opt.value ? "text-zinc-200 font-medium" : "text-zinc-400"}`}>
            {opt.label}
          </span>
        </button>
      ))}
    </div>
  );
}

function FieldMultiSelect({ field, values, onChange }: { field: InputField; values: string[]; onChange: (v: string[]) => void }) {
  const options = field.options ?? [];
  const toggle = (val: string) => {
    onChange(values.includes(val) ? values.filter((v) => v !== val) : [...values, val]);
  };
  return (
    <div className="space-y-1.5">
      {options.map((opt) => {
        const checked = values.includes(opt.value);
        return (
          <button
            type="button"
            key={opt.value}
            onClick={() => toggle(opt.value)}
            className={`flex items-center gap-3 rounded-lg border px-3.5 py-3 cursor-pointer transition-all w-full text-left
              ${checked
                ? "border-indigo-500/30 bg-indigo-500/6"
                : "border-zinc-700/40 bg-zinc-900/30 hover:border-zinc-600/60"
              }`}
          >
            <div className={`h-4 w-4 rounded border-2 flex items-center justify-center flex-shrink-0
              ${checked ? "border-indigo-400 bg-indigo-500" : "border-zinc-600"}`}>
              {checked && (
                <svg className="h-2.5 w-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              )}
            </div>
            <span className={`text-[15px] ${checked ? "text-zinc-200 font-medium" : "text-zinc-400"}`}>
              {opt.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function FieldConfirm({ field, value, onChange }: { field: InputField; value: boolean; onChange: (v: boolean) => void }) {
  const yesLabel = field.confirm_label ?? "Yes";
  const noLabel = field.deny_label ?? "No";
  return (
    <div className="flex gap-2">
      {[{ label: yesLabel, val: true }, { label: noLabel, val: false }].map(({ label, val }) => (
        <button
          key={label}
          type="button"
          onClick={() => onChange(val)}
          className={`flex-1 rounded-lg border px-4 py-2.5 text-[15px] font-medium transition-all
            ${value === val
              ? val
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                : "border-red-500/30 bg-red-500/8 text-red-300"
              : "border-zinc-700/40 bg-zinc-900/30 text-zinc-500 hover:border-zinc-600/60"
            }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function FieldInfo({ field }: { field: InputField }) {
  return (
    <div className="rounded-lg border border-zinc-700/30 bg-zinc-800/20 px-4 py-3">
      <Markdown className="text-[14px] text-zinc-400 leading-relaxed">{field.content ?? ""}</Markdown>
    </div>
  );
}

export default function HumanInputPrompt({ request, onRespond }: Props) {
  const hasFields = Boolean(request.input_fields?.length);
  const hasInfoBlocks = Boolean(request.info_blocks?.length);
  const hasUpcoming = Boolean(request.upcoming_actions?.length);

  const [fieldValues, setFieldValues] = useState<Record<string, unknown>>(() => {
    const init: Record<string, unknown> = {};
    request.input_fields?.forEach((f) => {
      if (f.type === "info") return;
      if (f.type === "multi_select") init[f.id] = f.defaults ?? [];
      else if (f.type === "confirm") init[f.id] = f.default ?? true;
      else if (f.type === "number") init[f.id] = f.default ?? f.min ?? 0;
      else init[f.id] = f.default ?? "";
    });
    return init;
  });

  const [freeText, setFreeText] = useState("");

  const updateField = (id: string, value: unknown) => {
    setFieldValues((prev) => ({ ...prev, [id]: value }));
  };

  const allRequiredFilled = () => {
    if (!request.input_fields) return true;
    return request.input_fields.every((f) => {
      if (f.type === "info") return true;
      if (f.required === false) return true;
      const val = fieldValues[f.id];
      if (val === undefined || val === null || val === "") return false;
      if (f.type === "multi_select" && Array.isArray(val) && val.length === 0) return false;
      return true;
    });
  };

  const handleSubmit = () => {
    onRespond(JSON.stringify({
      action: "submitted",
      fields: fieldValues,
      comments: freeText.trim() || null,
    }));
  };

  const handleFreeTextSubmit = () => {
    if (freeText.trim()) {
      onRespond(freeText.trim());
      setFreeText("");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="rounded-2xl border border-orange-500/20 overflow-hidden"
      style={{ background: "linear-gradient(135deg, rgba(249,115,22,0.04) 0%, transparent 60%)" }}
    >
      {/* ── Header with message ── */}
      <div className="flex items-start gap-3.5 px-5 py-4 border-b border-orange-500/10">
        <div className="relative flex-shrink-0 mt-0.5">
          <motion.div
            animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 rounded-full bg-orange-500/20"
          />
          <div className="relative flex h-9 w-9 items-center justify-center rounded-full
                          border border-orange-500/30 bg-orange-500/10">
            <svg className="h-4 w-4 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                    d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.12 48.12 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
            </svg>
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[13px] font-semibold uppercase tracking-wider text-orange-400/60 mb-1.5">
            Input Required
          </div>
          <Markdown className="text-[15px] text-zinc-300 leading-[1.7]">{request.message}</Markdown>
        </div>
      </div>

      {/* ── Info Blocks ── */}
      {hasInfoBlocks && (
        <div className="px-5 py-3 space-y-2.5 border-b border-zinc-800/40">
          {request.info_blocks!.map((block, i) => {
            const s = INFO_STYLES[block.style ?? "default"];
            return (
              <div key={i} className={`rounded-lg border ${s.border} ${s.bg} px-4 py-3`}>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[14px]">{s.icon}</span>
                  <span className={`text-[13px] font-semibold uppercase tracking-wider ${s.title}`}>
                    {block.title}
                  </span>
                </div>
                <Markdown className="text-[14px] text-zinc-400 leading-relaxed">{block.content}</Markdown>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Input Fields ── */}
      {hasFields && (
        <div className="px-5 py-4 space-y-4 border-b border-zinc-800/40">
          {request.input_fields!.map((field) => (
            <div key={field.id}>
              {field.type !== "info" && (
                <label className="text-[14px] font-semibold text-zinc-400 block mb-1.5">
                  {field.label}
                  {field.required !== false && field.type !== "confirm" && (
                    <span className="text-orange-400/60 ml-0.5">*</span>
                  )}
                </label>
              )}
              {field.type === "text" && (
                <FieldText field={field} value={String(fieldValues[field.id] ?? "")} onChange={(v) => updateField(field.id, v)} />
              )}
              {field.type === "number" && (
                <FieldNumber field={field} value={fieldValues[field.id] as number} onChange={(v) => updateField(field.id, v)} />
              )}
              {field.type === "select" && (
                <FieldSelect field={field} value={String(fieldValues[field.id] ?? "")} onChange={(v) => updateField(field.id, v)} />
              )}
              {field.type === "multi_select" && (
                <FieldMultiSelect field={field} values={(fieldValues[field.id] as string[]) ?? []} onChange={(v) => updateField(field.id, v)} />
              )}
              {field.type === "confirm" && (
                <FieldConfirm field={field} value={Boolean(fieldValues[field.id])} onChange={(v) => updateField(field.id, v)} />
              )}
              {field.type === "info" && (
                <>
                  <label className="text-[14px] font-semibold text-zinc-400 block mb-1.5">{field.label}</label>
                  <FieldInfo field={field} />
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Upcoming Actions ── */}
      {hasUpcoming && (
        <div className="px-5 py-3 border-b border-zinc-800/40">
          <div className="text-[13px] font-semibold uppercase tracking-wider text-zinc-500 mb-2.5">
            Next Steps
          </div>
          <div className="space-y-1.5">
            {request.upcoming_actions!.map((action, i) => (
              <div key={i} className="flex items-start gap-2.5 py-1.5">
                <div className="flex-shrink-0 mt-0.5 flex h-5 w-5 items-center justify-center
                                rounded-full border border-zinc-700/50 bg-zinc-800/50">
                  <span className="text-[11px] font-bold text-zinc-500">{i + 1}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-[14px] font-medium text-zinc-300">{action.action}</span>
                  <span className="text-[13px] text-zinc-600 ml-2">{action.scope}</span>
                </div>
                {action.tool && (
                  <span className="flex-shrink-0 text-xs font-mono text-zinc-600 bg-zinc-800/50
                                   px-1.5 py-0.5 rounded border border-zinc-800/40">
                    {action.tool}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Submit Area ── */}
      <div className="px-5 py-4">
        {hasFields ? (
          <div className="space-y-3">
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder="Additional notes or modifications (optional)..."
              rows={2}
              className="w-full rounded-lg border border-zinc-800/60 bg-zinc-900/40 px-3.5 py-2.5
                         text-[15px] text-zinc-300 placeholder-zinc-700 outline-none resize-none
                         focus:border-orange-500/30 transition-colors"
            />
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSubmit}
              disabled={!allRequiredFilled()}
              className="w-full rounded-lg bg-emerald-600 py-2.5 text-[15px] font-semibold text-white
                         transition-all hover:bg-emerald-500 shadow-lg shadow-emerald-900/20
                         disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Confirm & Continue
            </motion.button>
          </div>
        ) : (
          <div className="flex gap-2">
            <input
              type="text"
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && freeText.trim()) handleFreeTextSubmit();
              }}
              placeholder="Type a response..."
              className="flex-1 rounded-lg border border-zinc-800/60 bg-zinc-900/40 px-3.5 py-2.5
                         text-[15px] text-zinc-300 placeholder-zinc-700 outline-none
                         focus:border-orange-500/30 transition-colors"
            />
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleFreeTextSubmit}
              disabled={!freeText.trim()}
              className="rounded-lg bg-emerald-600 px-5 py-2.5 text-[15px] font-medium text-white
                         transition hover:bg-emerald-500 disabled:opacity-30"
            >
              Send
            </motion.button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
