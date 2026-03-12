"use client";

import { SessionInfo } from "@/lib/types";

interface SidebarProps {
  session: SessionInfo;
  toolsEnabled: Record<string, boolean>;
  onSendMessage?: (text: string) => void;
}

const STAGES = [
  { num: 1, name: "Greeting & Intent",      desc: "Welcome & intent" },
  { num: 2, name: "Identity Verification",  desc: "KYC & customer lookup" },
  { num: 3, name: "Loan Exploration",       desc: "Products & rates" },
  { num: 4, name: "Pre-Qualification",      desc: "Eligibility check" },
];

const CONNECTED_TOOLS = [
  { key: "customer_lookup", name: "Customer Lookup", always: true },
  { key: "loan_catalog",    name: "Loan Catalog",    always: true },
  { key: "eligibility",     name: "Eligibility Engine", always: true },
  { key: "google_drive",    name: "Google Drive",    always: false },
];

const PROMPTS = [
  "What loans do you offer?",
  "I'd like to apply for a personal loan",
  "I'm an existing Citibank customer",
  "Can I check if I'm eligible?",
];

const TEST_CUSTOMERS = [
  { name: "James Thompson", detail: "SW1A 1AA · 15/03/1985", status: "Pre-approved",     statusColor: "text-emerald-600 bg-emerald-50 border-emerald-100" },
  { name: "David Patel",    detail: "M1 4BT · 08/11/1978",   status: "Existing loan",    statusColor: "text-amber-600 bg-amber-50 border-amber-100" },
  { name: "Lucy Nguyen",    detail: "NE1 4ST · 05/04/2000",  status: "Part-time income", statusColor: "text-gray-500 bg-gray-50 border-gray-100" },
];

export default function Sidebar({ session, toolsEnabled, onSendMessage }: SidebarProps) {
  return (
    <aside className="w-64 shrink-0 bg-white border-r border-gray-100 flex flex-col overflow-y-auto">
      {/* Brand strip */}
      <div className="px-4 py-4 border-b border-gray-100">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-3">Session</p>
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-gray-400 w-12 flex-shrink-0">User</span>
            <span className="text-[11px] font-medium text-gray-700 truncate">{session.userId}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-gray-400 w-12 flex-shrink-0">Session</span>
            <span className="text-[11px] font-mono text-gray-500 truncate">{session.sessionId.slice(0, 14)}…</span>
          </div>
        </div>
      </div>

      <div className="flex-1 px-4 py-4 space-y-6">

        {/* Agent Stages */}
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2.5">Agent Stages</p>
          <div className="space-y-1.5">
            {STAGES.map((stage) => (
              <div key={stage.num} className="flex items-start gap-2.5 py-1.5">
                <div className="w-5 h-5 rounded-full bg-citi-blue flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                  <span className="text-[9px] font-bold text-white">{stage.num}</span>
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-gray-700 leading-tight">{stage.name}</p>
                  <p className="text-[10px] text-gray-400">{stage.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Connected Tools */}
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2.5">Connected Tools</p>
          <div className="space-y-1.5">
            {CONNECTED_TOOLS.map((tool) => {
              const enabled = tool.always || toolsEnabled[tool.key];
              return (
                <div key={tool.key} className="flex items-center gap-2">
                  <span
                    className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${enabled ? "bg-emerald-400 shadow-[0_0_4px_rgba(52,211,153,0.6)]" : "bg-gray-200"}`}
                  />
                  <span className={`text-[11px] font-medium ${enabled ? "text-gray-700" : "text-gray-300"}`}>
                    {tool.name}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        {/* Try These */}
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2.5">Try These</p>
          <div className="space-y-1.5">
            {PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => onSendMessage?.(prompt)}
                className="w-full text-left text-[11px] text-gray-600 bg-gray-50 hover:bg-blue-50 hover:text-citi-blue border border-gray-100 hover:border-blue-100 rounded-lg px-2.5 py-2 transition-all duration-150 leading-snug"
              >
                &ldquo;{prompt}&rdquo;
              </button>
            ))}
          </div>
        </section>

        {/* Test Customers */}
        <section>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2.5">Test Customers</p>
          <div className="space-y-2">
            {TEST_CUSTOMERS.map((c) => (
              <div
                key={c.name}
                className="bg-gray-50 border border-gray-100 rounded-xl px-3 py-2.5"
              >
                <p className="text-[12px] font-semibold text-gray-800 leading-tight">{c.name}</p>
                <p className="text-[10px] text-gray-400 mt-0.5">{c.detail}</p>
                <span className={`inline-block mt-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${c.statusColor}`}>
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </section>

      </div>
    </aside>
  );
}
