"use client";

import ReactMarkdown from "react-markdown";
import { ChatMessage } from "@/lib/types";
import ToolIndicator from "./ToolIndicator";

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[75%] ${
          isUser
            ? "bg-citi-blue text-white rounded-2xl rounded-br-md"
            : "bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-md shadow-sm"
        } px-4 py-3`}
      >
        {/* Agent name badge */}
        {!isUser && message.author && (
          <div className="text-xs text-citi-light font-medium mb-1">
            {formatAgentName(message.author)}
          </div>
        )}

        {/* Tool calls indicator — hide internal ADK tools like transfer_to_agent */}
        {!isUser && message.toolCalls && (() => {
          const visible = message.toolCalls.filter(
            (t) => t.status === "completed" && t.name !== "transfer_to_agent"
          );
          return visible.length > 0 ? <ToolIndicator tools={visible} /> : null;
        })()}

        {/* Message content */}
        {message.content ? (
          <div className={`prose prose-sm max-w-none ${isUser ? "prose-invert" : ""}`}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : (
          !isUser &&
          message.isStreaming && (
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <span
                className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: "0.1s" }}
              />
              <span
                className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: "0.2s" }}
              />
            </div>
          )
        )}

        {/* Streaming indicator */}
        {!isUser && message.isStreaming && message.content && (
          <span className="inline-block w-1.5 h-4 bg-citi-light animate-pulse ml-0.5" />
        )}
      </div>
    </div>
  );
}

function formatAgentName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
