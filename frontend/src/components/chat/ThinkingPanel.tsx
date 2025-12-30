"use client";

import { useState } from "react";

interface ThinkingPanelProps {
  thinking: string;
  isStreaming: boolean;
  phase?: string;
  phaseNumber?: number;
  totalPhases?: number;
}

export function ThinkingPanel({ 
  thinking, 
  isStreaming,
  phase,
  phaseNumber,
  totalPhases 
}: ThinkingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  
  if (!thinking && !isStreaming) return null;
  
  return (
    <div className="mb-4 border border-amber-500/30 rounded-lg bg-amber-950/20 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-amber-950/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isStreaming && (
            <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
          )}
          <span className="text-sm text-amber-400 font-medium">
            {isStreaming ? "Claude is thinking..." : "View Thinking Process"}
          </span>
          {phase && (
            <span className="text-xs text-amber-500 bg-amber-950/60 px-2 py-1 rounded">
              Phase {phaseNumber || 1}/{totalPhases || 3}: {phase}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-amber-400 transition-transform ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      
      {isExpanded && thinking && (
        <div className="px-4 pb-4 max-h-96 overflow-y-auto">
          <div className="bg-black/40 rounded p-3 border border-amber-500/20">
            <pre className="text-sm text-amber-200/80 whitespace-pre-wrap font-mono leading-relaxed">
              {thinking}
              {isStreaming && <span className="animate-pulse">▌</span>}
            </pre>
          </div>
          <p className="text-xs text-amber-500/70 mt-2 italic">
            This is Claude's internal reasoning process - showing how it thinks through the research.
          </p>
        </div>
      )}
    </div>
  );
}



