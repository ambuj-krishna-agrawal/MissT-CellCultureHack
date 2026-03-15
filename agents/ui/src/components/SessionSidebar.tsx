import { motion, AnimatePresence } from "framer-motion";
import type { SessionSummary } from "../types";

interface Props {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onNewChat: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  completed: "bg-emerald-400",
  stopped: "bg-amber-400",
  running: "bg-indigo-400",
  error: "bg-red-400",
  empty: "bg-zinc-600",
};

function timeAgo(ts: number | null): string {
  if (!ts) return "";
  const diff = (Date.now() / 1000) - ts;
  if (diff < 60) return "now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

export default function SessionSidebar({ sessions, activeSessionId, onSelect, onNewChat }: Props) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-zinc-800/40 bg-[#08080d]">
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-[13px] font-semibold uppercase tracking-[0.12em] text-zinc-600">
          Sessions
        </span>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onNewChat}
          className="flex h-6 w-6 items-center justify-center rounded-lg
                     text-zinc-500 transition-colors hover:text-zinc-300 hover:bg-zinc-800/50"
          title="New session"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        </motion.button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {sessions.length === 0 && (
          <p className="px-2 py-8 text-center text-[13px] text-zinc-700">No sessions yet</p>
        )}
        <AnimatePresence mode="popLayout">
          {sessions.map((s) => {
            const isActive = s.session_id === activeSessionId;
            return (
              <motion.button
                key={s.session_id}
                layout
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                onClick={() => onSelect(s.session_id)}
                className={`group flex w-full flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left mb-0.5
                            transition-all duration-200
                            ${isActive
                              ? "bg-indigo-500/8 border border-indigo-500/15"
                              : "border border-transparent hover:bg-zinc-800/30"}`}
              >
                <div className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${STATUS_COLORS[s.status] ?? "bg-zinc-600"}
                                    ${s.status === "running" ? "animate-pulse" : ""}`} />
                  <span className="truncate text-[14px] font-medium text-zinc-400 group-hover:text-zinc-200 transition-colors">
                    {s.name || "New session"}
                  </span>
                  <span className="ml-auto text-xs text-zinc-700 shrink-0">
                    {timeAgo(s.updated_at ?? s.created_at)}
                  </span>
                </div>
                {s.total_steps > 0 && (
                  <div className="pl-3.5 text-xs text-zinc-700">
                    {s.total_steps} step{s.total_steps !== 1 ? "s" : ""}
                  </div>
                )}
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>
    </aside>
  );
}
