"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import ChatPanel from "@/components/chat/ChatPanel";
import { useChat } from "@/hooks/useChat";
import { checkHealth } from "@/lib/api";

export default function Home() {
  const { messages, isLoading, error, activeTools, sendMessage, clearChat, session } =
    useChat();
  const [toolsEnabled, setToolsEnabled] = useState<Record<string, boolean>>({
    google_drive: false,
    google_docs: false,
    google_sheets: false,
  });

  useEffect(() => {
    checkHealth()
      .then((data) => {
        if (data.tools_enabled) {
          setToolsEnabled(data.tools_enabled as Record<string, boolean>);
        }
      })
      .catch(() => {
        // Backend not available yet
      });
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header onClearChat={clearChat} showAdmin={false} />
      <div className="flex flex-1 min-h-0">
        <Sidebar session={session} toolsEnabled={toolsEnabled} onSendMessage={sendMessage} />
        <main className="flex-1 flex flex-col min-h-0 min-w-0 bg-citi-gray">
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            error={error}
            activeTools={activeTools}
            onSendMessage={sendMessage}
          />
        </main>
      </div>
    </div>
  );
}
