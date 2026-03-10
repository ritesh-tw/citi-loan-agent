"use client";

import { useEffect, useRef, useState } from "react";
import { ChatMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import QuickForm from "./QuickForm";
import { ToolCall } from "@/lib/types";

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  activeTools: ToolCall[];
  onSendMessage: (text: string) => void;
}

export default function ChatPanel({
  messages,
  isLoading,
  error,
  activeTools,
  onSendMessage,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  // Detect which form to show based on conversation context
  const getFormType = (): "identity" | "personal_info" | "prequalification" | null => {
    // Find the last non-empty assistant message
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant" && m.content);
    if (!lastAssistant) return null;

    const content = lastAssistant.content?.toLowerCase() || "";
    const author = lastAssistant.author?.toLowerCase() || "";
    const lastTools = lastAssistant.toolCalls?.map((t) => t.name) || [];

    // === DON'T SHOW after results are presented ===
    if (
      content.includes("pre-qualified") || content.includes("indicative quote") ||
      content.includes("estimated monthly payment") || content.includes("unfortunately, we are unable")
    ) {
      return null;
    }

    // === DON'T SHOW for confirmation prompts ===
    if (
      content.includes("is this correct") || content.includes("please confirm") ||
      content.includes("everything correct") || content.includes("details are saved")
    ) {
      return null;
    }

    // === IDENTITY FORM (existing customer lookup) ===
    if (author.includes("identity")) {
      // Existing customer: asking for last name/postcode/DOB for lookup
      if (
        !content.includes("welcome back") &&
        !content.includes("are you currently") &&
        (content.includes("last name") || content.includes("surname"))
      ) {
        return "identity";
      }

      // New customer: collecting personal info (name, DOB, postcode, email, phone)
      const isCollectingPII =
        lastTools.includes("collect_personal_info") ||
        lastTools.includes("validate_personal_info") ||
        content.includes("full name") || content.includes("your name") ||
        content.includes("email") || content.includes("phone") ||
        content.includes("personal details") || content.includes("few details");

      if (isCollectingPII) {
        return "personal_info";
      }
    }

    // === PREQUALIFICATION FORM ===
    // Direct author match
    if (author.includes("prequalification")) {
      return "prequalification";
    }

    // Tool-based detection
    if (lastTools.includes("collect_application_info") || lastTools.includes("validate_application_info")) {
      return "prequalification";
    }

    // Content-based detection: any agent asking for employment, income, etc.
    const prequalKeywords = [
      "employment status", "annual income", "how much would you like to borrow",
      "loan amount", "repayment term", "residency status"
    ];
    if (prequalKeywords.some((kw) => content.includes(kw)) && content.includes("?")) {
      return "prequalification";
    }

    return null;
  };

  const formType = getFormType();

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-20">
            <div className="text-4xl mb-4">&#x1f3e6;</div>
            <h2 className="text-lg font-semibold text-gray-600 mb-2">
              Welcome to Citibank UK Loan Application
            </h2>
            <p className="text-sm max-w-md mx-auto mb-4">
              I can help you explore personal loan products, check your eligibility,
              and get an indicative loan offer. How can I help you today?
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg mx-auto">
              <button
                onClick={() => onSendMessage("What loans do you offer?")}
                className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full hover:bg-blue-50 hover:border-blue-200 transition-colors"
              >
                What loans do you offer?
              </button>
              <button
                onClick={() => onSendMessage("I'd like to apply for a personal loan")}
                className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full hover:bg-blue-50 hover:border-blue-200 transition-colors"
              >
                Apply for a loan
              </button>
              <button
                onClick={() => onSendMessage("Can I check if I'm eligible for a loan?")}
                className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full hover:bg-blue-50 hover:border-blue-200 transition-colors"
              >
                Check eligibility
              </button>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </>
        )}

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick form + input area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        {formType && !isLoading && (
          <div className="mb-2">
            <QuickForm onSubmit={onSendMessage} disabled={isLoading} formType={formType} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isLoading ? "Waiting for response..." : "Type your message or use the form above..."
            }
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-citi-light focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-2.5 bg-citi-blue text-white rounded-xl hover:bg-citi-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
