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

  return (
    <div className="mb-4 border border-zinc-700 rounded-lg bg-background-tertiary">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-zinc-800/50 rounded-lg transition-colors"
      >
        <span className="text-sm text-text-secondary flex items-center gap-2">
          <svg
            className={`w-4 h-4 transition-transform ${
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
          <span className="font-medium">{filteredSteps.length} reasoning steps</span>
        </span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-3 space-y-1.5 border-l-2 border-accent-primary/30 ml-4">
          {filteredSteps.map((step, index) => (
            <div
              key={index}
              className="text-sm text-text-secondary pl-4 py-1"
            >
              {step}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

