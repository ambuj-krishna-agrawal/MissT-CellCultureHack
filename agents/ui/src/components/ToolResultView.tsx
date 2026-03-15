/**
 * Thin dispatcher: parses the result and delegates to the
 * tool-specific renderer from the central registry.
 */

import { getToolConfig } from "./renderers/registry";

interface Props {
  toolName: string;
  result: unknown;
  args?: Record<string, unknown>;
}

function parse(raw: unknown): Record<string, unknown> {
  if (typeof raw === "string") {
    try { return JSON.parse(raw); } catch { return {}; }
  }
  if (raw && typeof raw === "object") return raw as Record<string, unknown>;
  return {};
}

export default function ToolResultView({ toolName, result, args }: Props) {
  if (result == null) return null;

  const data = parse(result);
  const { Renderer } = getToolConfig(toolName);

  return <Renderer data={data} args={args} />;
}
