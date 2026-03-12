"use client";

import Link from "next/link";

interface HeaderProps {
  onClearChat?: () => void;
  showAdmin?: boolean;
}

export default function Header({ onClearChat, showAdmin = true }: HeaderProps) {
  return (
    <header className="bg-citi-blue text-white shadow-[0_2px_12px_rgba(0,0,0,0.18)]">
      <div className="max-w-7xl mx-auto px-5 py-3.5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
          {/* Logo mark */}
          <div className="w-8 h-8 bg-white/15 border border-white/25 rounded-full flex items-center justify-center backdrop-blur-sm">
            <span className="text-white font-bold text-sm tracking-tight">C</span>
          </div>
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight leading-tight">Loan Application Agent</h1>
            <p className="text-[10px] text-blue-200 tracking-wide">Powered by ADK + Trustwise</p>
          </div>
        </Link>

        <div className="flex items-center gap-2">
          {showAdmin && (
            <Link
              href="/admin"
              className="px-3 py-1.5 text-xs font-medium bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg transition-all duration-150"
            >
              Admin
            </Link>
          )}
          {onClearChat && (
            <button
              onClick={onClearChat}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg transition-all duration-150"
            >
              <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
              </svg>
              New Chat
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
