"use client";

import { ToolCall } from "@/lib/types";

interface ToolIndicatorProps {
  tools: ToolCall[];
}

export default function ToolIndicator({ tools }: ToolIndicatorProps) {
  if (tools.length === 0) return null;

  return (
    <div className="space-y-1 mb-2">
      {tools.map((tool, i) => (
        <div
          key={`${tool.name}-${i}`}
          className="flex items-center gap-2 text-xs text-gray-500 px-3 py-1 bg-gray-50 rounded-lg"
        >
          {tool.status === "running" ? (
            <span className="w-3 h-3 border-2 border-citi-light border-t-transparent rounded-full animate-spin" />
          ) : (
            <span className="text-green-500">&#10003;</span>
          )}
          <span className="font-medium">{formatToolName(tool.name)}</span>
          {tool.status === "running" && (
            <span className="text-gray-400">running...</span>
          )}
        </div>
      ))}
    </div>
  );
}

function formatToolName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
