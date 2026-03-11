/**
 * API client for communicating with the ADK backend via SSE.
 */

import { ADKEvent } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BEARER_TOKEN = process.env.NEXT_PUBLIC_BEARER_TOKEN || "";

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (BEARER_TOKEN) {
    headers["Authorization"] = `Bearer ${BEARER_TOKEN}`;
  }
  return headers;
}

/**
 * Send a message via the /run_sse endpoint and stream events back.
 */
export async function sendMessageSSE(
  appName: string,
  userId: string,
  sessionId: string,
  message: string,
  onEvent: (event: ADKEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/run_sse`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        appName,
        userId,
        sessionId,
        newMessage: {
          role: "user",
          parts: [{ text: message }],
        },
        streaming: true,
      }),
    });

    if (!res.ok) {
      // Try to read the response body for detailed error info
      let detail = "";
      try {
        detail = await res.text();
      } catch {
        // ignore
      }
      throw new Error(detail || `API error: ${res.status} ${res.statusText}`);
    }

    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          const jsonStr = trimmed.slice(6);
          if (jsonStr === "[DONE]") continue;
          try {
            const event: ADKEvent = JSON.parse(jsonStr);
            onEvent(event);
          } catch {
            // Skip malformed JSON lines
          }
        }
      }
    }

    onComplete();
  } catch (error) {
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}

/**
 * Send a message via the synchronous /run endpoint.
 */
export async function sendMessage(
  appName: string,
  userId: string,
  sessionId: string,
  message: string
): Promise<ADKEvent[]> {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({
      appName,
      userId,
      sessionId,
      newMessage: {
        role: "user",
        parts: [{ text: message }],
      },
    }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

/**
 * Create a new session. Returns the server-assigned session ID
 * (Agent Engine assigns its own IDs).
 */
export async function createSession(
  appName: string,
  userId: string,
  sessionId: string
): Promise<string> {
  const res = await fetch(
    `${API_BASE}/apps/${appName}/users/${userId}/sessions/${sessionId}`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({}),
    }
  );

  if (!res.ok) {
    throw new Error(`Failed to create session: ${res.status}`);
  }

  const data = await res.json();
  return data.id || sessionId;
}

/**
 * Send a message via the simplified /api/chat endpoint.
 * This endpoint handles gateway policy errors gracefully and returns
 * a clean response with the error details.
 * Used as a fallback when SSE fails (e.g., gateway blocks the message).
 */
export interface ChatResponse {
  answer: string;
  session_id: string;
  agent: string;
  tools_used: string[];
  turn: number;
}

export async function sendChatMessage(
  message: string,
  sessionId?: string,
  newSession?: boolean
): Promise<ChatResponse> {
  const body: Record<string, unknown> = { question: message };
  if (sessionId) body.session_id = sessionId;
  if (newSession) body.new_session = true;

  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`Chat API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

/**
 * Check API health.
 */
export async function checkHealth(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
