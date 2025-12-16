"use client";

interface ThinkingIndicatorProps {
  status: string;
}

export function ThinkingIndicator({ status }: ThinkingIndicatorProps) {
  // Parse status for step info and remove trailing dots
  const stepMatch = status.match(/\(Step (\d+)\)/);
  const stepNum = stepMatch ? stepMatch[1] : null;
  // Remove step info AND trailing dots (...)
  const cleanStatus = status
    .replace(/\s*\(Step \d+\)/, "")
    .replace(/\.{2,}$/, "") // Remove 2+ trailing dots
    .trim();
  
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
          {/* Original animated dots */}
          <div className="flex gap-1">
            <span className="thinking-dot w-2 h-2 bg-accent-primary rounded-full"></span>
            <span className="thinking-dot w-2 h-2 bg-accent-primary rounded-full"></span>
            <span className="thinking-dot w-2 h-2 bg-accent-primary rounded-full"></span>
          </div>

          {/* Status text without trailing dots */}
          <div className="flex items-center gap-2">
            {stepNum && (
              <span className="text-xs font-medium bg-accent-primary/20 text-accent-primary px-2 py-0.5 rounded">
                Step {stepNum}
              </span>
            )}
            <span className="text-text-secondary text-sm">{cleanStatus}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

