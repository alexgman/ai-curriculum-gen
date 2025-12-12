"use client";

interface ThinkingIndicatorProps {
  status: string;
}

export function ThinkingIndicator({ status }: ThinkingIndicatorProps) {
  return (
    <div className="flex gap-4 max-w-4xl mx-auto">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center">
        <svg
          className="w-4 h-4 text-white animate-pulse"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
      </div>

      {/* Thinking Content */}
      <div className="flex-1">
        <div className="inline-flex items-center gap-3 px-4 py-3 bg-background-secondary rounded-2xl rounded-tl-sm">
          {/* Animated dots */}
          <div className="flex gap-1">
            <span className="thinking-dot w-2 h-2 bg-accent-primary rounded-full"></span>
            <span className="thinking-dot w-2 h-2 bg-accent-primary rounded-full"></span>
            <span className="thinking-dot w-2 h-2 bg-accent-primary rounded-full"></span>
          </div>

          {/* Status text */}
          <span className="text-text-secondary text-sm">{status}</span>
        </div>
      </div>
    </div>
  );
}

