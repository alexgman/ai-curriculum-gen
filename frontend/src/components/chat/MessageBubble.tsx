"use client";

import { Message } from "@/types/chat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ThinkingSteps } from "./ThinkingSteps";
import { MessageActions } from "./MessageActions";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""} group`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
          isUser
            ? "bg-accent-primary"
            : "bg-gradient-to-br from-purple-600 to-indigo-600"
        }`}
      >
        {isUser ? (
          <svg
            className="w-4 h-4 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <svg
            className="w-4 h-4 text-white"
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
        )}
      </div>

      {/* Message Content */}
      <div
        className={`flex-1 ${isUser ? "text-right" : ""} ${
          isUser ? "max-w-[80%]" : "max-w-full"
        }`}
      >
        {/* Thinking Steps (only for assistant) */}
        {!isUser && message.thinkingSteps && message.thinkingSteps.length > 0 && (
          <ThinkingSteps steps={message.thinkingSteps} />
        )}

        <div
          className={`inline-block px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-accent-primary text-white rounded-tr-sm"
              : "bg-background-secondary text-text-primary rounded-tl-sm"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || "..."}
              </ReactMarkdown>
              {message.isStreaming && <span className="typing-cursor ml-1"></span>}
            </div>
          )}
        </div>

        {/* Timestamp and Actions */}
        <div className="flex items-center gap-2 mt-1">
          <p className="text-xs text-text-muted">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
          
          {/* Actions for assistant messages */}
          {!isUser && message.content && !message.isStreaming && (
            <MessageActions content={message.content} messageId={message.id} />
          )}
        </div>
      </div>
    </div>
  );
}

