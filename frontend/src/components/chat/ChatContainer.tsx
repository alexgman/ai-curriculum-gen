"use client";

import { useRef, useEffect } from "react";
import { Message } from "@/types/chat";
import { MessageList } from "./MessageList";
import { InputArea } from "./InputArea";
import { ThinkingIndicator } from "./ThinkingIndicator";

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
  thinkingStatus: string | null;
  onSendMessage: (content: string) => void;
}

export function ChatContainer({
  messages,
  isLoading,
  thinkingStatus,
  onSendMessage,
}: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, thinkingStatus]);

  return (
    <div className="flex flex-col h-full bg-background-primary" suppressHydrationWarning>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-primary flex items-center justify-center">
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
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <div>
            <h1 className="font-semibold text-text-primary">Curriculum Research</h1>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
      >
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <MessageList messages={messages} />
        )}

        {/* Thinking indicator */}
        {thinkingStatus && <ThinkingIndicator status={thinkingStatus} />}
      </div>

      {/* Input */}
      <InputArea onSend={onSendMessage} isLoading={isLoading} />
    </div>
  );
}

function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-accent-primary/10 flex items-center justify-center mb-6">
        <svg
          className="w-8 h-8 text-accent-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-text-primary mb-3">
        Start Your Research
      </h2>
      <p className="text-text-secondary max-w-md text-sm">
        Enter an industry or career path to research competitor courses, curricula, and market trends.
      </p>
    </div>
  );
}

