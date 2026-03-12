"use client";

import { ToolCall } from "@/lib/types";

interface ToolIndicatorProps {
  tools: ToolCall[];
}

const TOOL_META: Record<string, { label: string; category: string; theme: "blue" | "violet" | "amber" | "emerald" | "slate" }> = {
  validate_personal_info:    { label: "Validate Personal Info",  category: "Identity",    theme: "blue" },
  collect_personal_info:     { label: "Collect Personal Info",   category: "Identity",    theme: "blue" },
  lookup_customer:           { label: "Customer Lookup",         category: "Identity",    theme: "blue" },
  get_loan_products:         { label: "Get Loan Products",       category: "Products",    theme: "violet" },
  get_product_details:       { label: "Get Product Details",     category: "Products",    theme: "violet" },
  validate_application_info: { label: "Validate Application",    category: "Application", theme: "amber" },
  collect_application_info:  { label: "Collect Application Info",category: "Application", theme: "amber" },
  run_prequalification:      { label: "Run Prequalification",    category: "Eligibility", theme: "emerald" },
  get_current_time:          { label: "Get Time",                category: "System",      theme: "slate" },
};

const THEME = {
  blue:    { pill: "bg-blue-50 border-blue-100 text-blue-700",    dot: "bg-blue-400",    badge: "bg-blue-100 text-blue-600" },
  violet:  { pill: "bg-violet-50 border-violet-100 text-violet-700", dot: "bg-violet-400", badge: "bg-violet-100 text-violet-600" },
  amber:   { pill: "bg-amber-50 border-amber-100 text-amber-700", dot: "bg-amber-400",   badge: "bg-amber-100 text-amber-600" },
  emerald: { pill: "bg-emerald-50 border-emerald-100 text-emerald-700", dot: "bg-emerald-400", badge: "bg-emerald-100 text-emerald-600" },
  slate:   { pill: "bg-slate-50 border-slate-100 text-slate-600", dot: "bg-slate-300",   badge: "bg-slate-100 text-slate-500" },
};

const DONE = { pill: "bg-emerald-50 border-emerald-100 text-emerald-700", badge: "bg-emerald-100 text-emerald-600" };

interface GroupedTool {
  name: string;
  count: number;
  status: "running" | "completed" | "error";
}

function groupTools(tools: ToolCall[]): GroupedTool[] {
  const groups: GroupedTool[] = [];
  for (const tool of tools) {
    const last = groups[groups.length - 1];
    if (last && last.name === tool.name) {
      last.count++;
      // If any instance is running, mark group as running
      if (tool.status === "running") last.status = "running";
    } else {
      groups.push({ name: tool.name, count: 1, status: tool.status ?? "completed" });
    }
  }
  return groups;
}

export default function ToolIndicator({ tools }: ToolIndicatorProps) {
  if (tools.length === 0) return null;

  const grouped = groupTools(tools);

  return (
    <div className="flex flex-wrap gap-1.5 mb-3">
      {grouped.map((tool, i) => {
        const meta    = TOOL_META[tool.name] ?? { label: tool.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()), category: "Tool", theme: "slate" as const };
        const isDone  = tool.status !== "running";
        const theme   = THEME[meta.theme as keyof typeof THEME];
        const pillCls = isDone ? DONE.pill : theme.pill;
        const badgeCls = isDone ? DONE.badge : theme.badge;

        return (
          <div
            key={`${tool.name}-${i}`}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium transition-all duration-200 ${pillCls}`}
          >
            {/* Status icon */}
            {isDone ? (
              <svg className="w-3 h-3 text-emerald-500 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-3 h-3 flex-shrink-0 animate-spin opacity-70" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}

            {/* Label */}
            <span>{meta.label}</span>

            {/* Count badge — only show if > 1 */}
            {tool.count > 1 && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${badgeCls}`}>
                ×{tool.count}
              </span>
            )}

            {/* Running text */}
            {!isDone && (
              <span className="opacity-50 font-normal">…</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
