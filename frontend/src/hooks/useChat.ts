"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { createSession, sendMessageSSE } from "@/lib/api";
import { ADKEvent, ChatMessage, SessionInfo, ToolCall } from "@/lib/types";

const APP_NAME = "loan_application_agent";

function generateSessionInfo(): SessionInfo {
  return {
    appName: APP_NAME,
    userId: `user_${uuidv4().slice(0, 8)}`,
    sessionId: `session_${uuidv4().slice(0, 8)}`,
  };
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTools, setActiveTools] = useState<ToolCall[]>([]);
  const [session, setSession] = useState<SessionInfo>({
    appName: APP_NAME,
    userId: "",
    sessionId: "",
  });

  const sessionCreated = useRef(false);
  const initialized = useRef(false);

  // Generate session IDs only on client side to avoid hydration mismatch
  useEffect(() => {
    if (!initialized.current) {
      setSession(generateSessionInfo());
      initialized.current = true;
    }
  }, []);

  const sessionRef = useRef(session);
  sessionRef.current = session;

  const initSession = useCallback(async () => {
    if (sessionCreated.current || !sessionRef.current.userId) return;
    try {
      // Agent Engine assigns its own session IDs — use the returned one
      const serverSessionId = await createSession(
        sessionRef.current.appName,
        sessionRef.current.userId,
        sessionRef.current.sessionId
      );
      if (serverSessionId !== sessionRef.current.sessionId) {
        setSession((prev) => ({ ...prev, sessionId: serverSessionId }));
        sessionRef.current = { ...sessionRef.current, sessionId: serverSessionId };
      }
      sessionCreated.current = true;
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      setError(null);
      setIsLoading(true);
      setActiveTools([]);

      // Ensure session exists
      await initSession();

      // Add user message
      const userMsg: ChatMessage = {
        id: uuidv4(),
        role: "user",
        content: text,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Placeholder for assistant response
      const assistantId = uuidv4();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: Date.now(),
        toolCalls: [],
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // ADK sends partial:true tokens AND a final partial:false event with the FULL text.
      // Track per-author to handle multi-agent flows (root → sub-agent).
      const partialsPerAuthor: Record<string, boolean> = {};
      let lastAuthor = "";

      await sendMessageSSE(
        sessionRef.current.appName,
        sessionRef.current.userId,
        sessionRef.current.sessionId,
        text,
        // onEvent
        (event: ADKEvent) => {
          if (!event.content?.parts) return;
          const author = event.author || "unknown";

          // When author changes, reset the assistant message content
          // so only the final responding agent's text is shown
          if (author !== lastAuthor && lastAuthor !== "") {
            // New agent is responding — clear previous agent's text
            // (e.g., root agent's "I'll transfer you" gets replaced by sub-agent's actual response)
            if (event.content.parts.some((p) => p.text)) {
              partialsPerAuthor[author] = false;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: "", author } : m
                )
              );
            }
          }
          lastAuthor = author;

          for (const part of event.content.parts) {
            // Handle text content
            if (part.text) {
              // Filter out raw function call text that LLM sometimes outputs
              if (/functions\.\w+\{/.test(part.text) || /transfer_to_agent/.test(part.text)) {
                continue;
              }

              if (event.partial === true) {
                partialsPerAuthor[author] = true;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + part.text, author }
                      : m
                  )
                );
              } else if (!partialsPerAuthor[author]) {
                // Complete response with no prior partials for this author
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + part.text, author }
                      : m
                  )
                );
              }
              // else: partial===false after partials — skip duplicate
            }

            // Handle tool calls — skip internal ADK routing tools
            if (part.functionCall && part.functionCall.name !== "transfer_to_agent") {
              const toolCall: ToolCall = {
                name: part.functionCall.name,
                args: part.functionCall.args,
                status: "running",
              };
              setActiveTools((prev) => [...prev, toolCall]);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        toolCalls: [...(m.toolCalls || []), toolCall],
                      }
                    : m
                )
              );
            }

            // Handle tool responses
            if (part.functionResponse) {
              setActiveTools((prev) =>
                prev.map((t) =>
                  t.name === part.functionResponse?.name
                    ? {
                        ...t,
                        status: "completed" as const,
                        response: part.functionResponse?.response,
                      }
                    : t
                )
              );
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        toolCalls: (m.toolCalls || []).map((t) =>
                          t.name === part.functionResponse?.name
                            ? {
                                ...t,
                                status: "completed" as const,
                                response: part.functionResponse?.response,
                              }
                            : t
                        ),
                      }
                    : m
                )
              );
            }
          }
        },
        // onError — show whatever error details we got from the server
        (err: Error) => {
          let errorContent = err.message || "Something went wrong.";

          // Try to parse JSON error body (e.g., gateway policy error)
          try {
            const parsed = JSON.parse(errorContent);
            if (parsed.error?.message) {
              errorContent = parsed.error.message;
            } else if (parsed.detail) {
              errorContent = parsed.detail;
            }
          } catch {
            // Not JSON — use raw message as-is
          }

          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: errorContent,
                    author: "System",
                    isStreaming: false,
                  }
                : m
            )
          );
          setIsLoading(false);
        },
        // onComplete
        () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isStreaming: false } : m
            )
          );
          setIsLoading(false);
          setActiveTools([]);
        }
      );
    },
    [isLoading, initSession]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setActiveTools([]);
    const newSession = generateSessionInfo();
    setSession(newSession);
    sessionCreated.current = false;
  }, []);

  return {
    messages,
    isLoading,
    error,
    activeTools,
    sendMessage,
    clearChat,
    session,
  };
}
