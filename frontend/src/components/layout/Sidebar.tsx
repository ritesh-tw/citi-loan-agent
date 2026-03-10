"use client";

import { SessionInfo } from "@/lib/types";

interface SidebarProps {
  session: SessionInfo;
  toolsEnabled: Record<string, boolean>;
  onSendMessage?: (text: string) => void;
}

export default function Sidebar({ session, toolsEnabled, onSendMessage }: SidebarProps) {
  const handlePromptClick = (text: string) => {
    if (onSendMessage) {
      onSendMessage(text);
    }
  };

  return (
    <aside className="w-64 shrink-0 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
      <div className="space-y-6">
        {/* Session Info */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Session
          </h3>
          <div className="text-xs text-gray-600 space-y-1">
            <p>
              <span className="font-medium">User:</span> {session.userId}
            </p>
            <p>
              <span className="font-medium">Session:</span>{" "}
              {session.sessionId.slice(0, 16)}...
            </p>
          </div>
        </div>

        {/* Agent Stages */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Agent Stages
          </h3>
          <div className="space-y-1.5">
            <ToolStatus name="Greeting & Intent" enabled={true} />
            <ToolStatus name="Identity Verification" enabled={true} />
            <ToolStatus name="Loan Exploration" enabled={true} />
            <ToolStatus name="Pre-Qualification" enabled={true} />
          </div>
        </div>

        {/* Tools */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Connected Tools
          </h3>
          <div className="space-y-1.5">
            <ToolStatus name="Customer Lookup" enabled={true} />
            <ToolStatus name="Loan Catalog" enabled={true} />
            <ToolStatus name="Eligibility Engine" enabled={true} />
            <ToolStatus name="Google Drive" enabled={toolsEnabled.google_drive} />
          </div>
        </div>

        {/* Demo Use Cases */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Try These
          </h3>
          <div className="space-y-2 text-xs text-gray-600">
            <p
              onClick={() => handlePromptClick("What loans do you offer?")}
              className="bg-white p-2 rounded border cursor-pointer hover:bg-blue-50 transition-colors"
            >
              &quot;What loans do you offer?&quot;
            </p>
            <p
              onClick={() => handlePromptClick("I'd like to apply for a personal loan")}
              className="bg-white p-2 rounded border cursor-pointer hover:bg-blue-50 transition-colors"
            >
              &quot;I&apos;d like to apply for a personal loan&quot;
            </p>
            <p
              onClick={() => handlePromptClick("I'm an existing Citibank customer")}
              className="bg-white p-2 rounded border cursor-pointer hover:bg-blue-50 transition-colors"
            >
              &quot;I&apos;m an existing Citibank customer&quot;
            </p>
            <p
              onClick={() => handlePromptClick("Can I check if I'm eligible for a loan?")}
              className="bg-white p-2 rounded border cursor-pointer hover:bg-blue-50 transition-colors"
            >
              &quot;Can I check if I&apos;m eligible?&quot;
            </p>
          </div>
        </div>

        {/* Test Customer Data */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Test Customers
          </h3>
          <div className="text-xs text-gray-500 space-y-1.5">
            <div className="bg-white p-2 rounded border">
              <p className="font-medium text-gray-700">James Thompson</p>
              <p>SW1A 1AA | 15/03/1985</p>
              <p className="text-green-600">Pre-approved</p>
            </div>
            <div className="bg-white p-2 rounded border">
              <p className="font-medium text-gray-700">David Patel</p>
              <p>M1 4BT | 08/11/1978</p>
              <p className="text-amber-600">Existing loan</p>
            </div>
            <div className="bg-white p-2 rounded border">
              <p className="font-medium text-gray-700">Lucy Nguyen</p>
              <p>NE1 4ST | 05/04/2000</p>
              <p className="text-gray-500">Part-time, low income</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function ToolStatus({ name, enabled }: { name: string; enabled: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`w-2 h-2 rounded-full ${
          enabled ? "bg-green-500" : "bg-gray-300"
        }`}
      />
      <span className={enabled ? "text-gray-700" : "text-gray-400"}>
        {name}
      </span>
    </div>
  );
}
