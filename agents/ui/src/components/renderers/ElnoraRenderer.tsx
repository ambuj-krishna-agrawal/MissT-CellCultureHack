import { motion } from "framer-motion";

function parseMarkdownTable(lines: string[], startIdx: number): { rows: string[][]; endIdx: number } | null {
  const headerLine = lines[startIdx];
  if (!headerLine || !headerLine.includes("|")) return null;

  const sepIdx = startIdx + 1;
  if (sepIdx >= lines.length) return null;
  const sepLine = lines[sepIdx];
  if (!sepLine || !sepLine.match(/^\s*\|[\s:|-]+\|\s*$/)) return null;

  const parseCells = (line: string) =>
    line.split("|").slice(1, -1).map((c) => c.trim());

  const rows: string[][] = [];
  rows.push(parseCells(headerLine));

  let i = sepIdx + 1;
  while (i < lines.length && lines[i].includes("|") && !lines[i].match(/^\s*$/)) {
    rows.push(parseCells(lines[i]));
    i++;
  }
  return { rows, endIdx: i };
}

function MarkdownTable({ rows }: { rows: string[][] }) {
  if (rows.length === 0) return null;
  const header = rows[0];
  const body = rows.slice(1);

  return (
    <div className="my-3 overflow-x-auto rounded-lg border border-white/[0.06]">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-white/[0.06] bg-white/[0.02]">
            {header.map((cell, i) => (
              <th key={i} className="px-4 py-2.5 text-left font-semibold text-zinc-300 whitespace-nowrap">
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, ri) => (
            <tr key={ri} className="border-b border-white/[0.03] last:border-b-0">
              {row.map((cell, ci) => (
                <td key={ci} className="px-4 py-2 text-zinc-400 whitespace-nowrap">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ElnoraRenderer({ data }: { data: Record<string, unknown> }) {
  const status = String(data.status ?? "unknown");
  const protocolText = String(data.protocol_text ?? "");
  const source = String(data.source ?? "elnora");

  const isSuccess = status === "success";

  const renderProtocol = () => {
    if (!protocolText) return null;
    const lines = protocolText.split("\n");
    const elements: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];

      const table = parseMarkdownTable(lines, i);
      if (table) {
        elements.push(<MarkdownTable key={`tbl-${i}`} rows={table.rows} />);
        i = table.endIdx;
        continue;
      }

      if (line.startsWith("## ")) {
        elements.push(
          <div key={i} className="text-[15px] font-bold text-white mt-4 mb-1.5">
            {line.replace(/^##\s*/, "")}
          </div>
        );
      } else if (line.startsWith("### ")) {
        elements.push(
          <div key={i} className="text-[13px] font-semibold text-[#a78bfa] mt-4 mb-1">
            {line.replace(/^###\s*/, "")}
          </div>
        );
      } else if (line.match(/^\d+\.\s+\*\*/)) {
        const cleaned = line.replace(/\*\*/g, "");
        const match = cleaned.match(/^(\d+\.)\s*(.*)/);
        if (match) {
          elements.push(
            <div key={i} className="flex gap-2 mt-3 mb-1">
              <span className="text-indigo-400 font-semibold text-[14px] shrink-0">{match[1]}</span>
              <span className="text-[14px] font-semibold text-zinc-200">{match[2]}</span>
            </div>
          );
        } else {
          elements.push(<div key={i} className="text-[13.5px] text-zinc-300 pl-4">{cleaned}</div>);
        }
      } else if (line.startsWith("**") && line.endsWith("**")) {
        elements.push(
          <div key={i} className="font-semibold text-[14px] text-zinc-200 mt-2">
            {line.replace(/\*\*/g, "")}
          </div>
        );
      } else if (line.startsWith("- ") || line.startsWith("• ")) {
        elements.push(
          <div key={i} className="flex gap-2 pl-4 text-[13px] text-zinc-400 leading-relaxed">
            <span className="text-zinc-600 shrink-0">•</span>
            <span>{line.replace(/^[-•]\s*/, "")}</span>
          </div>
        );
      } else if (line.match(/^\d+\.\s/)) {
        elements.push(
          <div key={i} className="pl-4 text-[13px] text-zinc-400 leading-relaxed">
            {line}
          </div>
        );
      } else if (line.startsWith("⚠️") || line.startsWith("⚠")) {
        elements.push(
          <div key={i} className="flex items-start gap-2 mt-2 rounded-lg bg-orange-500/5 border border-orange-500/10 px-3 py-2">
            <span className="shrink-0">⚠️</span>
            <span className="text-[13px] text-orange-300/90">{line.replace(/^⚠️?\s*/, "")}</span>
          </div>
        );
      } else {
        elements.push(<div key={i} className="text-[13.5px] text-zinc-400 leading-relaxed">{line || <br />}</div>);
      }

      i++;
    }

    return elements;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <motion.div
          initial={{ scale: 0.5, rotate: -10 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 300 }}
          className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white text-[14px] font-bold"
        >
          E
        </motion.div>
        <span className="text-[15px] font-semibold text-zinc-100">Elnora AI</span>
        <span className="text-[14px] text-zinc-500">Protocol Expert</span>
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className={`ml-auto inline-flex items-center rounded-full px-2.5 py-1 text-[13px] font-medium border ${
            isSuccess
              ? "bg-[#34d399]/10 text-[#34d399] border-[#34d399]/20"
              : "bg-[#f97316]/10 text-[#f97316] border-[#f97316]/20"
          }`}
        >
          {isSuccess ? "✓ Response" : status}
        </motion.span>
      </div>

      {protocolText && (
        <div className="rounded-xl bg-white/[0.015] border border-white/[0.06] px-5 py-4 max-h-[28rem] overflow-y-auto">
          {renderProtocol()}
        </div>
      )}

      <div className="text-[13px] text-zinc-600">
        Powered by {source} · Protocol recommendations
      </div>
    </div>
  );
}
