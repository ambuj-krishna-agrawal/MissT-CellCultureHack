import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAgent } from "./hooks/useAgent";
import { useSessions } from "./hooks/useSessions";
import ChatInput from "./components/ChatInput";
import PipelineView from "./components/PipelineView";
import SessionSidebar from "./components/SessionSidebar";
import SystemFacts from "./components/SystemFacts";

interface HealthInfo {
  provider: string;
  model: string;
  mock_mode: boolean;
}

export default function App() {
  const {
    run, sendQuery, stopRun, resumeRun, sendHumanResponse,
    loadSession: loadSessionState, newSession,
  } = useAgent();
  const { sessions, refresh: refreshSessions, loadSession: fetchSession } = useSessions();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setHealth({ provider: d.provider, model: d.model, mock_mode: d.mock_mode }))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (run.status === "completed" || run.status === "stopped") {
      refreshSessions();
    }
  }, [run.status, refreshSessions]);

  const handleSessionSelect = useCallback(async (sessionId: string) => {
    const data = await fetchSession(sessionId);
    if (data) loadSessionState(data);
  }, [fetchSession, loadSessionState]);

  const handleNewChat = useCallback(async () => {
    await newSession();
    refreshSessions();
  }, [newSession, refreshSessions]);

  const isRunning = run.status === "running" || run.status === "waiting_human_input";

  return (
    <div className="flex h-screen bg-[var(--bg)]">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 256, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <SessionSidebar
              sessions={sessions}
              activeSessionId={run.session_id}
              onSelect={handleSessionSelect}
              onNewChat={handleNewChat}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-zinc-800/30 px-5 h-12">
          <div className="flex items-center gap-3">
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setSidebarOpen((p) => !p)}
              className="flex h-7 w-7 items-center justify-center rounded-lg
                         text-zinc-500 transition-colors hover:text-zinc-300 hover:bg-zinc-800/40"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </motion.button>

            {/* Brand */}
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg
                              bg-gradient-to-br from-indigo-500/20 to-violet-500/10
                              border border-indigo-500/20">
                <svg className="h-4 w-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                        d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-base font-semibold text-zinc-100 tracking-tight">
                  CellPilot
                </span>
                <span className="text-xs font-medium text-zinc-600">
                  Agent
                </span>
              </div>
            </div>
          </div>

          {/* Right: model badge */}
          {health && (
            <div className="flex items-center gap-2 rounded-lg border border-zinc-800/40 px-2.5 py-1">
              <span className="text-xs text-zinc-600">Model</span>
              <span className="font-mono text-[13px] text-zinc-400">{health.model}</span>
            </div>
          )}
        </header>

        <SystemFacts />

        <PipelineView
          run={run}
          onHumanResponse={sendHumanResponse}
          onStop={stopRun}
          onResume={resumeRun}
        />

        <ChatInput
          onSend={sendQuery}
          disabled={isRunning}
        />
      </div>
    </div>
  );
}
