export type EventType =
  | "thinking_delta"
  | "content_delta"
  | "step_start"
  | "step_complete"
  | "run_start"
  | "run_complete"
  | "run_stopped"
  | "human_input_requested"
  | "session_history"
  | "robot_event"
  | "error";

export interface AgentEvent {
  event_type: EventType;
  data: Record<string, unknown>;
  timestamp: number;
  event_id: string;
}

export interface PipelineStep {
  step_id: string;
  step_number: number;
  tool_name: string;
  arguments: Record<string, unknown>;
  reasoning: string | null;
  thinking: string | null;
  result: string | null;
  status: "running" | "completed" | "error";
  duration_ms: number | null;
}

export type Segment =
  | { kind: "reasoning"; text: string; forStep: number }
  | { kind: "thinking"; text: string }
  | { kind: "step"; step: PipelineStep }
  | { kind: "output"; text: string }
  | { kind: "query"; text: string };

// ── Human Input Schema ──────────────────────────────────────────────────

export interface InputFieldOption {
  value: string;
  label: string;
}

export interface InputField {
  id: string;
  type: "text" | "number" | "select" | "multi_select" | "confirm" | "info";
  label: string;
  required?: boolean;
  // text
  placeholder?: string;
  default?: unknown;
  // number
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  // select / multi_select
  options?: InputFieldOption[];
  defaults?: string[];
  // confirm
  confirm_label?: string;
  deny_label?: string;
  // info
  content?: string;
}

export interface InfoBlock {
  title: string;
  content: string;
  style?: "default" | "warning" | "success" | "info";
}

export interface UpcomingAction {
  action: string;
  scope: string;
  tool?: string;
}

export interface HumanInputRequest {
  message: string;
  input_fields: InputField[] | null;
  info_blocks: InfoBlock[] | null;
  upcoming_actions: UpcomingAction[] | null;
}

// ── Robot Events ────────────────────────────────────────────────────────

export interface RobotEvent {
  robot_step: number;
  name: string;
  message: string;
}

// ── Run & Session ───────────────────────────────────────────────────────

export interface RunState {
  session_id: string | null;
  run_id: string | null;
  query: string;
  segments: Segment[];
  status: "idle" | "running" | "completed" | "stopped" | "error" | "waiting_human_input";
  duration_ms: number | null;
  error: string | null;
  stepCount: number;
  humanInputRequest: HumanInputRequest | null;
  robotEvents: Record<string, RobotEvent[]>;
}

export interface SessionSummary {
  session_id: string;
  name: string;
  status: string;
  run_count: number;
  total_steps: number;
  created_at: number | null;
  updated_at: number | null;
}

export interface SessionRun {
  run_id: string;
  query: string;
  status: string;
  steps: Array<{
    id: string;
    step_number: number;
    tool_name: string;
    arguments: Record<string, unknown>;
    reasoning: string | null;
    thinking: string | null;
    result: unknown;
    status: string;
    duration_ms: number | null;
  }>;
  final_output: string | null;
  started_at: number;
  completed_at: number | null;
  duration_ms: number | null;
}

export interface SessionDetail {
  session_id: string;
  name: string;
  runs: SessionRun[];
  provider: string;
  model: string;
  mock_mode: boolean;
  created_at: number;
  updated_at: number;
}

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";
