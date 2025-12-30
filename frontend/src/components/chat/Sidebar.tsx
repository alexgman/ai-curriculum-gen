"use client";

import { useState, useRef, useEffect } from "react";
import { ResearchSession } from "@/types/chat";

// Sidebar props for session management
export interface SidebarProps {
  sessions: ResearchSession[];
  currentSession: ResearchSession | null;
  onSelectSession: (session: ResearchSession) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onUpdateTitle?: (sessionId: string, newTitle: string) => void;
}

export function Sidebar({
  sessions,
  currentSession,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onUpdateTitle,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Focus input when editing starts
  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);
  
  const startEditing = (session: ResearchSession) => {
    setEditingId(session.id);
    setEditValue(session.title);
  };
  
  const finishEditing = (sessionId: string) => {
    if (editValue.trim() && editValue !== sessions.find(s => s.id === sessionId)?.title) {
      onUpdateTitle?.(sessionId, editValue.trim());
    }
    setEditingId(null);
    setEditValue("");
  };
  
  const cancelEditing = () => {
    setEditingId(null);
    setEditValue("");
  };
  return (
    <aside className="w-64 bg-background-secondary border-r border-zinc-800 flex flex-col" suppressHydrationWarning>
      {/* Logo */}
      <div className="p-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent-primary flex items-center justify-center">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
          </div>
          <div>
            <h1 className="font-bold text-text-primary">Curriculum Builder</h1>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewSession}
          className="w-full flex items-center gap-2 px-4 py-2.5 bg-background-tertiary hover:bg-zinc-700 rounded-lg transition-colors text-text-primary"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          <span className="text-sm font-medium">New Research</span>
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <p className="text-xs text-text-muted uppercase tracking-wider px-2 mb-2">
          Recent
        </p>
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`group relative rounded-lg ${
              currentSession?.id === session.id
                ? "bg-accent-primary/20"
                : "hover:bg-background-tertiary"
            }`}
          >
            {editingId === session.id ? (
              // Edit mode
              <div className="px-3 py-2.5">
                <input
                  ref={inputRef}
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      finishEditing(session.id);
                    } else if (e.key === "Escape") {
                      cancelEditing();
                    }
                  }}
                  onBlur={() => finishEditing(session.id)}
                  className="w-full bg-background-tertiary border border-accent-primary text-sm text-text-primary px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-accent-primary"
                />
              </div>
            ) : (
              // View mode
              <button
                onClick={() => onSelectSession(session)}
                className={`w-full text-left px-3 py-2.5 pr-16 transition-colors ${
                  currentSession?.id === session.id
                    ? "text-accent-primary"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                <p className="text-sm font-medium truncate">{session.title}</p>
                <p className="text-xs text-text-muted">
                  {new Date(session.createdAt).toLocaleDateString()}
                </p>
              </button>
            )}
            
            {/* Edit and Delete buttons */}
            {editingId !== session.id && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {onUpdateTitle && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startEditing(session);
                    }}
                    className="p-1.5 hover:bg-accent-primary/20 rounded"
                    title="Edit title"
                  >
                    <svg
                      className="w-4 h-4 text-text-secondary hover:text-accent-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                      />
                    </svg>
                  </button>
                )}
                {onDeleteSession && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete "${session.title}"?`)) {
                        onDeleteSession(session.id);
                      }
                    }}
                    className="p-1.5 hover:bg-red-500/20 rounded"
                    title="Delete session"
                  >
                    <svg
                      className="w-4 h-4 text-red-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                )}
              </div>
            )}
          </div>
        ))}

        {sessions.length === 0 && (
          <p className="text-sm text-text-muted text-center py-8">
            No research sessions yet
          </p>
        )}
      </div>

    </aside>
  );
}

