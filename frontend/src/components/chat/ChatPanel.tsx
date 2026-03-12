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
  // activeTools available if needed for global tool status display
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

  // Extract pre-qual values mentioned anywhere in conversation history
  const extractPrequalValues = (): Record<string, string> => {
    const result: Record<string, string> = {};
    const userText = messages
      .filter((m) => m.role === "user")
      .map((m) => m.content || "")
      .join(" ");
    const allText = messages.map((m) => m.content || "").join(" ");
    const lower = allText.toLowerCase();

    // Annual income: "65K", "£65,000", "earn 65000"
    const incomeMatch = userText.match(/(?:earn|income|salary|make)\s*[£]?\s*([\d,]+)\s*k?\b/i);
    if (incomeMatch) {
      let val = incomeMatch[1].replace(/,/g, "");
      if (/k/i.test(incomeMatch[0].slice(incomeMatch[0].lastIndexOf(incomeMatch[1])))) val = String(parseInt(val) * 1000);
      result.annual_income = val;
    }
    const incomeKMatch = userText.match(/(?:earn|income|salary)\s*[£]?\s*(\d+)k/i);
    if (incomeKMatch && !result.annual_income) result.annual_income = String(parseInt(incomeKMatch[1]) * 1000);

    // Loan amount: "loan of 35K", "borrow £25,000", "then 25K"
    const loanMatch = userText.match(/(?:loan(?:\s+of)?|borrow|want\s+(?:a\s+)?(?:loan\s+(?:of|for)?)?|then)\s*[£]?\s*([\d,]+)\s*(k?)/i);
    if (loanMatch) {
      let val = loanMatch[1].replace(/,/g, "");
      if (loanMatch[2]?.toLowerCase() === "k") val = String(parseInt(val) * 1000);
      result.loan_amount = val;
    }

    // Loan purpose
    if (lower.includes("debt consolidation")) result.loan_purpose = "debt_consolidation";
    else if (lower.includes("home improvement")) result.loan_purpose = "home_improvement";
    else if (lower.includes("car loan") || lower.includes("car purchase")) result.loan_purpose = "car";
    else if (lower.includes("holiday")) result.loan_purpose = "holiday";
    else if (lower.includes("wedding")) result.loan_purpose = "wedding";
    else if (lower.includes("personal loan") || lower.includes("personal")) result.loan_purpose = "personal";

    // Employment
    if (/full.?time/i.test(lower)) result.employment_status = "full_time";
    else if (/part.?time/i.test(lower)) result.employment_status = "part_time";
    else if (/self.?employ/i.test(lower)) result.employment_status = "self_employed";
    else if (/retired/i.test(lower)) result.employment_status = "retired";
    else if (/unemployed/i.test(lower)) result.employment_status = "unemployed";

    // Repayment term
    const termMatch = userText.match(/(\d+)\s*months?/i);
    if (termMatch) result.repayment_term = termMatch[1];

    // Residency
    if (/uk\s*resident/i.test(lower)) result.residency_status = "uk_resident";
    else if (/uk\s*visa|visa\s*holder/i.test(lower)) result.residency_status = "uk_visa";
    else if (/non.?resident/i.test(lower)) result.residency_status = "non_resident";

    return result;
  };

  // Detect which form to show based on conversation context
  const getFormType = (): "identity" | "personal_info" | "prequalification" | null => {
    // Find the last non-empty assistant message
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant" && m.content);
    if (!lastAssistant) return null;

    const content = lastAssistant.content?.toLowerCase() || "";
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
      content.includes("everything correct") || content.includes("details are saved") ||
      content.includes("let me now check")
    ) {
      return null;
    }

    // === IDENTITY FORM (existing customer lookup — last name + postcode + DOB) ===
    if (
      (content.includes("last name") || content.includes("surname")) &&
      !content.includes("full name") &&
      !content.includes("email")
    ) {
      return "identity";
    }

    // === PERSONAL INFO FORM (new customer PII — name, DOB, postcode, email, phone) ===
    // Priority: if agent is asking for PII fields, always show this form (not pre-qual)
    const isCollectingPII =
      lastTools.includes("collect_personal_info") ||
      lastTools.includes("validate_personal_info") ||
      content.includes("full name") ||
      content.includes("date of birth") ||
      content.includes("email address") ||
      content.includes("phone number") ||
      content.includes("postcode") ||
      content.includes("personal details") ||
      (content.includes("few details") && !lastTools.includes("collect_application_info"));

    if (isCollectingPII) {
      return "personal_info";
    }

    // === PREQUALIFICATION FORM ===
    // Tool-based detection (most reliable)
    if (lastTools.includes("collect_application_info") || lastTools.includes("validate_application_info")) {
      return "prequalification";
    }

    // Content-based: asking specifically for pre-qual fields (not just mentioning them)
    const prequalKeywords = [
      "employment status", "repayment term", "residency status",
      "how much would you like to borrow", "how long would you like"
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
      <div className="border-t border-gray-100 bg-white px-4 pt-3 pb-4">
        {formType && !isLoading && (
          <div className="mb-2.5">
            <QuickForm
              onSubmit={onSendMessage}
              disabled={isLoading}
              formType={formType}
              initialValues={formType === "prequalification" ? extractPrequalValues() : {}}
            />
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2 items-center">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isLoading ? "Agent is responding…" : "Type your message or use the form above…"
            }
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-citi-light/40 focus:border-citi-light disabled:bg-gray-50 disabled:text-gray-400 bg-gray-50 placeholder:text-gray-400 transition-all"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="flex items-center gap-1.5 px-5 py-2.5 bg-citi-blue text-white text-sm font-semibold rounded-xl hover:bg-citi-light transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            {isLoading ? (
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            )}
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
