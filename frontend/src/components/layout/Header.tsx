"use client";

import Link from "next/link";

interface HeaderProps {
  onClearChat?: () => void;
  showAdmin?: boolean;
}

export default function Header({ onClearChat, showAdmin = true }: HeaderProps) {
  return (
    <header className="bg-citi-blue text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
          <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
            <span className="text-citi-blue font-bold text-sm">C</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold">Loan Application Agent</h1>
            <p className="text-xs text-blue-200">Powered by ADK + Trustwise</p>
          </div>
        </Link>
        <div className="flex items-center gap-2">
          {showAdmin && (
            <Link
              href="/admin"
              className="px-3 py-1.5 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
            >
              Admin
            </Link>
          )}
          {onClearChat && (
            <button
              onClick={onClearChat}
              className="px-3 py-1.5 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
            >
              New Chat
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
