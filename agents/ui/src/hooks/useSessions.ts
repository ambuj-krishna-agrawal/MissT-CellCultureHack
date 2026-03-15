import { useCallback, useEffect, useState } from "react";
import type { SessionDetail, SessionSummary } from "../types";

export function useSessions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/sessions");
      const data = await res.json();
      setSessions(data.sessions ?? []);
    } catch {
      /* ignore */
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string): Promise<SessionDetail | null> => {
    setLoading(true);
    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      const data = await res.json();
      if (data.error) return null;
      return data as SessionDetail;
    } catch {
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { sessions, loading, refresh, loadSession };
}
