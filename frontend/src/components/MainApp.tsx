"use client";

import { useState, useEffect } from "react";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { Sidebar } from "@/components/chat/Sidebar";
import { Message, ResearchSession } from "@/types/chat";
import { generateUUID } from "@/lib/uuid";

export default function MainApp() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Get current session from sessions array
  const currentSession = sessions.find(s => s.id === currentSessionId) || null;
  const messages = currentSession?.messages || [];
  const thinkingStatus = currentSession?.thinkingStatus || null;

  // Create a new session
  const createNewSession = () => {
    const newSession: ResearchSession = {
      id: generateUUID(),
      title: "New Research",
      createdAt: new Date().toISOString(),
      messages: [],
      thinkingStatus: null,
    };
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  // Update current session
  const updateCurrentSession = (updates: Partial<ResearchSession>) => {
    if (!currentSessionId) return;
    
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSessionId ? { ...s, ...updates } : s
      )
    );
  };

  // Add message to current session
  const addMessage = (message: Message) => {
    if (!currentSessionId) return;
    
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSessionId
          ? { ...s, messages: [...(s.messages || []), message] }
          : s
      )
    );
  };

  // Update message in current session
  const updateMessage = (messageId: string, updates: Partial<Message>) => {
    if (!currentSessionId) return;
    
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSessionId
          ? {
              ...s,
              messages: (s.messages || []).map((m) =>
                m.id === messageId ? { ...m, ...updates } : m
              ),
            }
          : s
      )
    );
  };

  // Set thinking status for current session
  const setSessionThinking = (status: string | null, sessionId?: string) => {
    const targetId = sessionId || currentSessionId;
    if (!targetId) return;
    
    setSessions((prev) =>
      prev.map((s) =>
        s.id === targetId ? { ...s, thinkingStatus: status } : s
      )
    );
  };

  // Generate session title using Claude API
  const generateSessionTitle = async (sessionId: string, userMessage: string) => {
    if (!userMessage || !userMessage.trim()) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      const response = await fetch(`${apiUrl}/api/v1/sessions/generate-title`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });
      
      if (response.ok) {
        const data = await response.json();
        updateSessionById(sessionId, { title: data.title });
      } else {
        const words = userMessage.split(" ").slice(0, 6).join(" ");
        const title = words.length > 50 ? words.slice(0, 47) + "..." : words || "Research";
        updateSessionById(sessionId, { title });
      }
    } catch {
      const words = userMessage.split(" ").slice(0, 6).join(" ");
      const title = words.length > 50 ? words.slice(0, 47) + "..." : words || "Research";
      updateSessionById(sessionId, { title });
    }
  };

  const updateSessionById = (sessionId: string, updates: Partial<ResearchSession>) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, ...updates } : s))
    );
  };

  // Load a different session
  const loadSession = (session: ResearchSession) => {
    setCurrentSessionId(session.id);
  };

  // Delete a session
  const deleteSession = (sessionId: string) => {
    if (sessionId === currentSessionId) {
      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== sessionId);
        
        if (filtered.length > 0) {
          setCurrentSessionId(filtered[0].id);
          return filtered;
        } else {
          const newSession: ResearchSession = {
            id: generateUUID(),
            title: "New Research",
            createdAt: new Date().toISOString(),
            messages: [],
            thinkingStatus: null,
          };
          setCurrentSessionId(newSession.id);
          return [newSession];
        }
      });
    } else {
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    }
  };

  // Send message to backend
  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading || !currentSessionId) return;

    const userMessage: Message = {
      id: generateUUID(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMessage);
    setIsLoading(true);
    
    const activeSessionId = currentSessionId;
    setSessionThinking("Starting research...", activeSessionId || undefined);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      const response = await fetch(`${apiUrl}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          session_id: currentSessionId,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";
      let assistantMessageId = generateUUID();
      let thinkingMessages: string[] = [];

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "thinking") {
                const stepInfo = data.step ? ` (Step ${data.step})` : "";
                setSessionThinking(`${data.status || data.tool || "Processing..."}${stepInfo}`, activeSessionId || undefined);
              } else if (data.type === "node") {
                const nodeName = data.node;
                const stepNum = data.step || thinkingMessages.length + 1;
                
                if (nodeName === "reasoning") {
                  let reasoningText = data.reasoning || "Analyzing query and planning research strategy";
                  if (data.content) {
                    reasoningText = data.content.replace(/^[💭🔍📊🔧✍️Reasoning:\s]*/g, "").trim();
                  }
                  if (reasoningText.length > 100) {
                    reasoningText = reasoningText.slice(0, 100) + "...";
                  }
                  thinkingMessages.push(`Step ${stepNum}: Planning - ${reasoningText}`);
                  setSessionThinking(`Planning next action... (Step ${stepNum})`, activeSessionId || undefined);
                } else if (nodeName === "tool_executor") {
                  const toolCall = data.tool_call;
                  if (toolCall) {
                    const toolName = toolCall.name;
                    const args = toolCall.arguments || {};
                    const argStr = args.query || args.url || args.industry || Object.values(args)[0] || "";
                    const shortArg = typeof argStr === 'string' ? argStr.slice(0, 40) : String(argStr).slice(0, 40);
                    thinkingMessages.push(`Step ${stepNum}: Running ${toolName}("${shortArg}")`);
                    setSessionThinking(`Running ${toolName}... (Step ${stepNum})`, activeSessionId || undefined);
                  } else {
                    thinkingMessages.push(`Step ${stepNum}: Executing tool...`);
                    setSessionThinking(`Executing tool... (Step ${stepNum})`, activeSessionId || undefined);
                  }
                } else if (nodeName === "reflection") {
                  let reflectionText = data.reflection || "Validating results";
                  if (data.content) {
                    reflectionText = data.content.replace(/^[💭🔍📊🔧✍️Reflection:\s]*/g, "").trim();
                  }
                  if (reflectionText.length > 80) {
                    reflectionText = reflectionText.slice(0, 80) + "...";
                  }
                  const result = data.tool_result;
                  const status = result?.success ? "✓" : "✗";
                  thinkingMessages.push(`Step ${stepNum}: Validate ${status} - ${reflectionText}`);
                  setSessionThinking(`Validating results... (Step ${stepNum})`, activeSessionId || undefined);
                } else if (nodeName === "response") {
                  thinkingMessages.push(`Step ${stepNum}: Generating final response`);
                  setSessionThinking(`Writing response... (Step ${stepNum})`, activeSessionId || undefined);
                }

                if (data.content && data.content.trim() && !data.content.startsWith("💭") && !data.content.startsWith("🔍") && !data.content.startsWith("📊")) {
                  assistantContent = data.content;
                  
                  setSessions((prevSessions) => {
                    return prevSessions.map((session) => {
                      if (session.id !== currentSessionId) return session;
                      
                      const currentMessages = session.messages || [];
                      const existingIndex = currentMessages.findIndex(msg => msg.id === assistantMessageId);
                      
                      let updatedMessages;
                      if (existingIndex >= 0) {
                        updatedMessages = currentMessages.map((msg) =>
                          msg.id === assistantMessageId
                            ? { 
                                ...msg, 
                                content: assistantContent, 
                                thinkingSteps: [...thinkingMessages],
                                isStreaming: false 
                              }
                            : msg
                        );
                      } else {
                        const newMessage: Message = {
                          id: assistantMessageId,
                          role: "assistant" as const,
                          content: assistantContent,
                          timestamp: new Date().toISOString(),
                          isStreaming: false,
                          thinkingSteps: [...thinkingMessages],
                        };
                        updatedMessages = [...currentMessages, newMessage];
                      }
                      
                      return { ...session, messages: updatedMessages };
                    });
                  });
                }
              } else if (data.type === "complete") {
                setSessionThinking(null, activeSessionId || undefined);
                if (activeSessionId) {
                  generateSessionTitle(activeSessionId, content).catch(console.error);
                }
              } else if (data.type === "error") {
                throw new Error(data.message || "Unknown error");
              }
            } catch (e: any) {
              if (e.message && e.message.includes("Error")) {
                throw e;
              }
            }
          }
        }
      }

      if (!assistantContent || assistantContent.trim() === "") {
        throw new Error("No response received from server");
      }
    } catch (error: any) {
      console.error("Error sending message:", error);
      const errorMsg = error.message || "Unknown error";
      const errorMessage: Message = {
        id: generateUUID(),
        role: "assistant",
        content: `**Error**: ${errorMsg}\n\nPlease make sure:\n1. API keys are set in .env file\n2. Backend server is running\n3. If accessing remotely, set NEXT_PUBLIC_API_URL in frontend/.env.local`,
        timestamp: new Date().toISOString(),
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
      setSessionThinking(null, activeSessionId || undefined);
    }
  };

  // Initialize sessions from localStorage
  useEffect(() => {
    try {
      const savedSessions = localStorage.getItem("research_sessions");
      if (savedSessions) {
        const parsed = JSON.parse(savedSessions);
        if (parsed && parsed.length > 0) {
          setSessions(parsed);
          setCurrentSessionId(parsed[0].id);
          setIsInitialized(true);
          return;
        }
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
    }
    
    // Create initial session if none exist
    const newSession: ResearchSession = {
      id: generateUUID(),
      title: "New Research",
      createdAt: new Date().toISOString(),
      messages: [],
      thinkingStatus: null,
    };
    setSessions([newSession]);
    setCurrentSessionId(newSession.id);
    setIsInitialized(true);
  }, []);

  // Save sessions to localStorage
  useEffect(() => {
    if (isInitialized && sessions.length > 0) {
      try {
        localStorage.setItem("research_sessions", JSON.stringify(sessions));
      } catch (error) {
        console.error("Error saving sessions:", error);
      }
    }
  }, [sessions, isInitialized]);

  return (
    <div className="flex h-screen">
      <Sidebar
        sessions={sessions}
        currentSession={currentSession}
        onSelectSession={loadSession}
        onNewSession={createNewSession}
        onDeleteSession={deleteSession}
      />

      <main className="flex-1 flex flex-col">
        <ChatContainer
          messages={messages}
          isLoading={isLoading}
          thinkingStatus={thinkingStatus}
          onSendMessage={sendMessage}
        />
      </main>
    </div>
  );
}

