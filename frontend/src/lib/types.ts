/**
 * TypeScript types matching ADK event structures.
 */

export interface ADKPart {
  text?: string;
  functionCall?: {
    name: string;
    args: Record<string, unknown>;
  };
  functionResponse?: {
    name: string;
    response: Record<string, unknown>;
  };
}

export interface ADKContent {
  parts: ADKPart[];
  role: string;
}

export interface ADKEvent {
  id: string;
  timestamp: number;
  author: string;
  content?: ADKContent;
  partial?: boolean;
  actions?: {
    stateDelta?: Record<string, unknown>;
    artifactDelta?: Record<string, unknown>;
  };
  invocationId?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  author?: string;
  timestamp: number;
  toolCalls?: ToolCall[];
  isStreaming?: boolean;
}

export interface ToolCall {
  name: string;
  args?: Record<string, unknown>;
  response?: Record<string, unknown>;
  status: "running" | "completed" | "error";
}

export interface SessionInfo {
  appName: string;
  userId: string;
  sessionId: string;
}
