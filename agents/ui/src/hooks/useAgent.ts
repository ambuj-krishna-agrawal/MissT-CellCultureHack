import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentEvent, ConnectionStatus, HumanInputRequest, PipelineStep,
  RobotEvent, RunState, Segment, SessionDetail, SessionRun,
} from "../types";

const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`;

const EMPTY_RUN: RunState = {
  session_id: null,
  run_id: null,
  query: "",
  segments: [],
  status: "idle",
  duration_ms: null,
  error: null,
  stepCount: 0,
  humanInputRequest: null,
  robotEvents: {},
};

function runToSegments(run: SessionRun): Segment[] {
  const segs: Segment[] = [];
  segs.push({ kind: "query", text: run.query });
  for (const step of run.steps) {
    if (step.reasoning) {
      segs.push({ kind: "reasoning", text: step.reasoning, forStep: step.step_number });
    }
    segs.push({
      kind: "step",
      step: {
        step_id: step.id,
        step_number: step.step_number,
        tool_name: step.tool_name,
        arguments: step.arguments,
        reasoning: step.reasoning,
        thinking: step.thinking,
        result: step.result != null
          ? (typeof step.result === "string" ? step.result : JSON.stringify(step.result))
          : null,
        status: step.status === "completed" ? "completed" : step.status === "error" ? "error" : "running",
        duration_ms: step.duration_ms,
      },
    });
  }
  if (run.final_output) {
    segs.push({ kind: "output", text: run.final_output });
  }
  return segs;
}

export function useAgent() {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [run, setRun] = useState<RunState>(EMPTY_RUN);
  const wsRef = useRef<WebSocket | null>(null);
  const stepCountRef = useRef(0);

  const handleEvent = useCallback((event: AgentEvent) => {
    const { event_type, data } = event;

    switch (event_type) {
      case "session_history": {
        const sessionId = data.session_id as string;
        const runs = (data.runs ?? []) as SessionRun[];
        const segments: Segment[] = [];
        let totalSteps = 0;
        for (const r of runs) {
          segments.push(...runToSegments(r));
          totalSteps += r.steps.length;
        }
        stepCountRef.current = totalSteps;
        setRun((prev) => ({
          ...prev,
          session_id: sessionId,
          segments,
          stepCount: totalSteps,
        }));
        break;
      }

      case "run_start": {
        const newSessionId = data.session_id as string;
        const newRunId = data.run_id as string;
        const query = data.query as string;
        const isResume = !!data.resume;
        const resumedFromStep = (data.resumed_from_step as number) ?? 0;

        if (isResume) {
          stepCountRef.current = resumedFromStep;
          setRun((prev) => ({
            ...prev,
            session_id: newSessionId,
            run_id: newRunId,
            status: "running",
            error: null,
            humanInputRequest: null,
            segments: prev.segments.filter(
              (seg) => !(seg.kind === "step" && seg.step.status === "error")
            ),
          }));
        } else {
          setRun((prev) => {
            const isSameSession = prev.session_id === newSessionId;
            const baseSegments = isSameSession ? [...prev.segments] : [];
            baseSegments.push({ kind: "query", text: query });

            return {
              ...prev,
              session_id: newSessionId,
              run_id: newRunId,
              query,
              segments: baseSegments,
              status: "running",
              error: null,
              humanInputRequest: null,
              stepCount: isSameSession ? prev.stepCount : 0,
              robotEvents: isSameSession ? prev.robotEvents : {},
            };
          });
        }
        break;
      }

      case "thinking_delta": {
        const delta = (data.delta as string) ?? "";
        setRun((prev) => {
          const segs = [...prev.segments];
          const last = segs[segs.length - 1];
          if (last && last.kind === "thinking") {
            segs[segs.length - 1] = { ...last, text: last.text + delta };
          } else {
            segs.push({ kind: "thinking", text: delta });
          }
          return { ...prev, segments: segs };
        });
        break;
      }

      case "content_delta": {
        const delta = (data.delta as string) ?? "";
        setRun((prev) => {
          const segs = [...prev.segments];
          const last = segs[segs.length - 1];
          if (last && last.kind === "reasoning") {
            segs[segs.length - 1] = { ...last, text: last.text + delta };
          } else if (last && last.kind === "output") {
            segs[segs.length - 1] = { ...last, text: last.text + delta };
          } else {
            segs.push({ kind: "reasoning", text: delta, forStep: stepCountRef.current + 1 });
          }
          return { ...prev, segments: segs };
        });
        break;
      }

      case "step_start": {
        stepCountRef.current += 1;
        const step: PipelineStep = {
          step_id: data.step_id as string,
          step_number: data.step_number as number,
          tool_name: data.tool_name as string,
          arguments: data.arguments as Record<string, unknown>,
          reasoning: (data.reasoning as string) ?? null,
          thinking: (data.thinking as string) ?? null,
          result: null,
          status: "running",
          duration_ms: null,
        };
        setRun((prev) => {
          const segs = [...prev.segments];
          const last = segs[segs.length - 1];
          if (last && last.kind === "reasoning") {
            segs[segs.length - 1] = { ...last, forStep: step.step_number };
          }
          segs.push({ kind: "step", step });
          return { ...prev, segments: segs, stepCount: prev.stepCount + 1, status: "running" };
        });
        break;
      }

      case "step_complete": {
        const stepId = data.step_id as string;
        setRun((prev) => ({
          ...prev,
          segments: prev.segments.map((seg) => {
            if (seg.kind === "step" && seg.step.step_id === stepId) {
              return {
                ...seg,
                step: {
                  ...seg.step,
                  result: data.result as string,
                  status: "completed" as const,
                  duration_ms: (data.duration_ms as number) ?? null,
                },
              };
            }
            return seg;
          }),
        }));
        break;
      }

      case "robot_event": {
        const stepId = data.step_id as string;
        const robotEvt: RobotEvent = {
          robot_step: (data.robot_step as number) ?? 0,
          name: (data.name as string) ?? "",
          message: (data.message as string) ?? "",
        };
        setRun((prev) => ({
          ...prev,
          robotEvents: {
            ...prev.robotEvents,
            [stepId]: [...(prev.robotEvents[stepId] ?? []), robotEvt],
          },
        }));
        break;
      }

      case "human_input_requested":
        setRun((prev) => ({
          ...prev,
          status: "waiting_human_input",
          humanInputRequest: {
            message: (data.message as string) ?? "",
            input_fields: (data.input_fields as HumanInputRequest["input_fields"]) ?? null,
            info_blocks: (data.info_blocks as HumanInputRequest["info_blocks"]) ?? null,
            upcoming_actions: (data.upcoming_actions as HumanInputRequest["upcoming_actions"]) ?? null,
          },
        }));
        break;

      case "run_complete": {
        const completion = data.completion as Record<string, unknown> | undefined;
        let outputText = "";
        if (completion) {
          const parts: string[] = [];
          if (completion.summary) parts.push(String(completion.summary));
          if (completion.status && completion.status !== "completed") {
            parts.push(`**Status:** ${completion.status}`);
          }
          const findings = completion.key_findings as string[] | undefined;
          if (findings?.length) {
            parts.push("\n**Key Findings:**\n" + findings.map((f) => `- ${f}`).join("\n"));
          }
          const nextSteps = completion.next_steps as string[] | undefined;
          if (nextSteps?.length) {
            parts.push("\n**Next Steps:**\n" + nextSteps.map((s) => `- ${s}`).join("\n"));
          }
          outputText = parts.join("\n");
        }
        setRun((prev) => {
          const segs = [...prev.segments];
          // Strip trailing reasoning/thinking that weren't consumed by a step
          while (segs.length > 0) {
            const last = segs[segs.length - 1];
            if (last.kind === "reasoning" || last.kind === "thinking") {
              segs.pop();
            } else {
              break;
            }
          }
          if (outputText) {
            segs.push({ kind: "output", text: outputText });
          }
          return {
            ...prev,
            segments: segs,
            status: "completed",
            duration_ms: (data.duration_ms as number) ?? null,
            humanInputRequest: null,
          };
        });
        break;
      }

      case "run_stopped":
        setRun((prev) => ({
          ...prev,
          segments: prev.segments.map((seg) => {
            if (seg.kind === "step" && seg.step.status === "running") {
              return { ...seg, step: { ...seg.step, status: "error" as const } };
            }
            return seg;
          }),
          status: "stopped",
          duration_ms: (data.duration_ms as number) ?? null,
          humanInputRequest: null,
        }));
        break;

      case "error":
        setRun((prev) => ({
          ...prev,
          status: "error",
          error: (data.error as string) ?? "Unknown error",
          humanInputRequest: null,
        }));
        break;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      if (wsRef.current.readyState === WebSocket.CONNECTING) wsRef.current.close();
      wsRef.current = null;
    }
    setStatus("connecting");
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    ws.onopen = () => { if (wsRef.current !== ws) return; setStatus("connected"); };
    ws.onmessage = (ev) => {
      if (wsRef.current !== ws) return;
      try { handleEvent(JSON.parse(ev.data)); } catch { /* ignore */ }
    };
    ws.onerror = () => { if (wsRef.current !== ws) return; setStatus("error"); };
    ws.onclose = () => { if (wsRef.current !== ws) return; setStatus("disconnected"); wsRef.current = null; };
  }, [handleEvent]);

  const sendQuery = useCallback((query: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect();
      return;
    }
    setRun((prev) => ({
      ...prev,
      status: "running",
      error: null,
      humanInputRequest: null,
    }));
    const sessionId = run.session_id;
    wsRef.current.send(JSON.stringify({ query, session_id: sessionId }));
  }, [connect, run.session_id]);

  const stopRun = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    }
    setRun((prev) => ({
      ...prev,
      segments: prev.segments.map((seg) =>
        seg.kind === "step" && seg.step.status === "running"
          ? { ...seg, step: { ...seg.step, status: "error" as const } }
          : seg
      ),
      status: "stopped",
      humanInputRequest: null,
    }));
  }, []);

  const resumeRun = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect();
      return;
    }
    const sessionId = run.session_id;
    if (!sessionId) return;
    wsRef.current.send(JSON.stringify({ action: "resume", session_id: sessionId }));
  }, [connect, run.session_id]);

  const sendHumanResponse = useCallback((response: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "human_response", response }));
      setRun((prev) => ({ ...prev, status: "running", humanInputRequest: null }));
    }
  }, []);

  const loadSession = useCallback((session: SessionDetail) => {
    const segments: Segment[] = [];
    let totalSteps = 0;
    for (const r of session.runs) {
      segments.push(...runToSegments(r));
      totalSteps += r.steps.length;
    }
    stepCountRef.current = totalSteps;

    const latestRun = session.runs[session.runs.length - 1];
    const latestStatus = latestRun?.status ?? "idle";

    setRun({
      session_id: session.session_id,
      run_id: latestRun?.run_id ?? null,
      query: latestRun?.query ?? "",
      segments,
      status: latestStatus === "completed" ? "completed"
            : latestStatus === "stopped" ? "stopped"
            : "idle",
      duration_ms: latestRun?.duration_ms ?? null,
      error: null,
      stepCount: totalSteps,
      humanInputRequest: null,
      robotEvents: {},
    });
  }, []);

  const newSession = useCallback(async () => {
    try {
      const res = await fetch("/api/sessions", { method: "POST" });
      const data = await res.json();
      const sessionId = data.session_id as string;
      setRun({ ...EMPTY_RUN, session_id: sessionId });
      return sessionId;
    } catch {
      const fallbackId = Math.random().toString(36).slice(2, 14);
      setRun({ ...EMPTY_RUN, session_id: fallbackId, robotEvents: {} });
      return fallbackId;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      const ws = wsRef.current;
      if (ws) { ws.onopen = null; ws.onclose = null; ws.onerror = null; ws.onmessage = null; ws.close(); wsRef.current = null; }
    };
  }, [connect]);

  return { status, run, sendQuery, stopRun, resumeRun, sendHumanResponse, loadSession, newSession, connect };
}
