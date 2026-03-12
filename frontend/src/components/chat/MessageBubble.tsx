"use client";

import ReactMarkdown from "react-markdown";
import { ChatMessage } from "@/lib/types";
import ToolIndicator from "./ToolIndicator";

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end mb-5">
        <div className="max-w-[72%] bg-citi-blue text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-sm">
          <div className="prose prose-sm prose-invert max-w-none text-sm leading-relaxed">
            <ReactMarkdown>{message.content ?? ""}</ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  // Agent message
  const visibleTools = (message.toolCalls ?? []).filter((t) => t.name !== "transfer_to_agent");

  return (
    <div className="flex justify-start mb-5 gap-2.5">
      {/* Agent avatar */}
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-citi-blue flex items-center justify-center shadow-sm mt-0.5">
        <span className="text-white text-[11px] font-bold tracking-tight">C</span>
      </div>

      <div className="max-w-[76%]">
        {/* Agent name */}
        {message.author && (
          <div className="text-[11px] text-gray-400 font-medium mb-1.5 ml-0.5 tracking-wide uppercase">
            {formatAgentName(message.author)}
          </div>
        )}

        <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm shadow-[0_1px_8px_rgba(0,0,0,0.06)] px-4 py-3">
          {/* Tool calls */}
          {visibleTools.length > 0 && <ToolIndicator tools={visibleTools} />}

          {/* Message content */}
          {message.content ? (
            <div className="prose prose-sm max-w-none text-gray-800 leading-relaxed">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          ) : (
            message.isStreaming && (
              <div className="flex items-center gap-1 py-1">
                <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }} />
                <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
              </div>
            )
          )}

          {/* Streaming cursor */}
          {message.isStreaming && message.content && (
            <span className="inline-block w-0.5 h-3.5 bg-citi-light animate-pulse ml-0.5 align-middle" />
          )}
        </div>
      </div>
    </div>
  );
}

function formatAgentName(name: string): string {
  const labels: Record<string, string> = {
    loan_application_agent: "Loan Application Agent",
  };
  return labels[name] ?? name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
