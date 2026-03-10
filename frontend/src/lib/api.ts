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
      throw new Error(`API error: ${res.status} ${res.statusText}`);
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
 * Create a new session.
 */
export async function createSession(
  appName: string,
  userId: string,
  sessionId: string
): Promise<void> {
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
}

/**
 * Check API health.
 */
export async function checkHealth(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
