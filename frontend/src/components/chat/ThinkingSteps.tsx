"use client";

import { useState } from "react";

interface ThinkingStepsProps {
  steps: string[];
}

export function ThinkingSteps({ steps }: ThinkingStepsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Filter out reflection messages - only show reasoning steps
  const filteredSteps = steps.filter(
    (step) => !step.toLowerCase().startsWith("reflection:")
  );

  if (filteredSteps.length === 0) return null;

  // Combine all steps into one block for better display
  const combinedThinking = filteredSteps.join("\n\n");
  const previewLength = 200;
  const hasMore = combinedThinking.length > previewLength;
  const preview = combinedThinking.slice(0, previewLength).replace(/\n/g, ' ').trim();

  return (
    <div className="mb-4 border border-zinc-700 rounded-lg bg-background-tertiary overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-start gap-2 text-left hover:bg-zinc-800/50 transition-colors"
      >
        <svg
          className={`w-4 h-4 mt-0.5 flex-shrink-0 transition-transform ${
            isExpanded ? "rotate-90" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
        <div className="flex-1 min-w-0">
          <span className="text-sm font-medium text-text-secondary">
            {filteredSteps.length} reasoning {filteredSteps.length === 1 ? 'step' : 'steps'}
          </span>
          {!isExpanded && preview && (
            <p className="text-xs text-text-muted mt-1 line-clamp-2">
              {preview}{hasMore ? '...' : ''}
            </p>
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-zinc-700/50">
          <div className="mt-3 max-h-[400px] overflow-y-auto">
            <div className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
              {combinedThinking}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

