"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { Sidebar } from "@/components/chat/Sidebar";
import { Message, ResearchSession } from "@/types/chat";
import { generateUUID } from "@/lib/uuid";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Get or generate a persistent client ID for session isolation
function getClientId(): string {
  const STORAGE_KEY = 'curriculum_builder_client_id';
  if (typeof window === 'undefined') return '';
  
  let clientId = localStorage.getItem(STORAGE_KEY);
  if (!clientId) {
    clientId = generateUUID();
    localStorage.setItem(STORAGE_KEY, clientId);
  }
  return clientId;
}

export default function MainApp() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Use ref to track latest session ID to avoid stale closure issues
  const currentSessionIdRef = useRef<string | null>(null);
  
  // Client ID for session isolation (persisted in localStorage)
  const clientIdRef = useRef<string>('');
  
  // Keep ref in sync with state
  useEffect(() => {
    currentSessionIdRef.current = currentSessionId;
  }, [currentSessionId]);
  
  // Initialize client ID on mount
  useEffect(() => {
    clientIdRef.current = getClientId();
  }, []);

  // Get current session from sessions array
  const currentSession = sessions.find(s => s.id === currentSessionId) || null;
  const messages = currentSession?.messages || [];
  const thinkingStatus = currentSession?.thinkingStatus || null;

  // Fetch sessions from backend API (filtered by client_id)
  const fetchSessions = useCallback(async () => {
    try {
      const clientId = clientIdRef.current || getClientId();
      const response = await fetch(`${API_URL}/api/v1/sessions?client_id=${encodeURIComponent(clientId)}`);
      if (response.ok) {
        const data = await response.json();
        const dbSessions: ResearchSession[] = data.sessions.map((s: any) => ({
          id: s.id,
          title: s.title || "New Research",
          createdAt: s.created_at,
          messages: [],
          thinkingStatus: null,
        }));
        return dbSessions;
      }
    } catch (error) {
      console.warn("Failed to fetch sessions from API:", error);
    }
    return [];
  }, []);

  // Fetch session details including messages
  const fetchSessionDetails = useCallback(async (sessionId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/sessions/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        return {
          id: data.id,
          title: data.title || "New Research",
          createdAt: data.created_at,
          messages: data.messages.map((m: any) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            timestamp: m.created_at,
            thinkingSteps: m.thinking_steps || [],
          })),
          thinkingStatus: null,
        } as ResearchSession;
      }
    } catch (error) {
      console.warn("Failed to fetch session details:", error);
    }
    return null;
  }, []);

  // Create a new session (API)
  const createNewSession = async () => {
    const newSessionId = generateUUID();
    const newSession: ResearchSession = {
      id: newSessionId,
      title: "New Research",
      createdAt: new Date().toISOString(),
      messages: [],
      thinkingStatus: null,
    };
    
    // Update ref IMMEDIATELY to avoid race conditions
    currentSessionIdRef.current = newSessionId;
    
    // Add to local state immediately for responsiveness
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    
    // Backend will create the session when first message is sent
    console.log(`📌 Created new session: ${newSessionId}`);
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
      const response = await fetch(`${API_URL}/api/v1/sessions/generate-title`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });
      
      if (response.ok) {
        const data = await response.json();
        updateSessionById(sessionId, { title: data.title });
        
        // Also update the backend
        await fetch(`${API_URL}/api/v1/sessions/${sessionId}?title=${encodeURIComponent(data.title)}`, {
          method: "PUT",
        });
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

  // Load a different session - fetch full details from backend
  const loadSession = async (session: ResearchSession) => {
    setCurrentSessionId(session.id);
    
    // If session has no messages loaded, fetch from backend
    if (!session.messages || session.messages.length === 0) {
      const details = await fetchSessionDetails(session.id);
      if (details && details.messages.length > 0) {
        setSessions((prev) =>
          prev.map((s) =>
            s.id === session.id ? { ...s, messages: details.messages } : s
          )
        );
        console.log(`📂 Loaded ${details.messages.length} messages for session ${session.id}`);
      }
    }
  };

  // Delete a session (also from backend)
  const deleteSession = async (sessionId: string) => {
    // Delete from backend
    try {
      await fetch(`${API_URL}/api/v1/sessions/${sessionId}`, {
        method: "DELETE",
      });
    } catch (error) {
      console.warn("Failed to delete session from backend:", error);
    }
    
    // Update local state
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
    // Use ref for latest session ID to avoid race conditions
    const sessionId = currentSessionIdRef.current || currentSessionId;
    if (!content.trim() || isLoading || !sessionId) return;

    const userMessage: Message = {
      id: generateUUID(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMessage);
    setIsLoading(true);
    
    // Use the session ID from ref (most up-to-date)
    const activeSessionId = sessionId;
    setSessionThinking("Starting research...", activeSessionId || undefined);

    try {
      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          session_id: activeSessionId,  // Use the reliable session ID
          client_id: clientIdRef.current || getClientId(),  // For session isolation
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
      let sseBuffer = "";  // Buffer for incomplete SSE messages

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append to buffer using streaming mode to handle multi-byte characters
        sseBuffer += decoder.decode(value, { stream: true });
        
        // SSE messages are separated by double newlines (\n\n)
        // Split and keep any incomplete message in the buffer
        const messages = sseBuffer.split("\n\n");
        sseBuffer = messages.pop() || "";  // Keep incomplete part for next chunk
        
        for (const message of messages) {
          // Each SSE message can have multiple lines (event:, data:, id:, etc.)
          const lines = message.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const jsonStr = line.slice(6);
                if (!jsonStr.trim()) continue;  // Skip empty data lines
                const data = JSON.parse(jsonStr);

                // Handle session sync from backend - CRITICAL for context persistence
                if (data.type === "session" && data.session_id) {
                  console.log(`🔗 Backend session_id received: ${data.session_id}`);
                  // If frontend has a different session_id, we need to update the backend's reference
                  // But more importantly, we need to make sure subsequent messages use the same session_id
                } else if (data.type === "thinking") {
                  // Show detailed progress from backend tools - these are the real status updates
                  const stepInfo = data.step ? ` (Step ${data.step})` : "";
                  const status = data.status || data.tool || "Processing";
                  setSessionThinking(`${status}${stepInfo}`, activeSessionId || undefined);
                } else if (data.type === "node") {
                  const nodeName = data.node;
                  const stepNum = data.step || thinkingMessages.length + 1;
                  
                  // Only add to thinking messages log, don't overwrite the live status
                  // The "thinking" events from backend tools have more detailed progress
                  if (nodeName === "reasoning") {
                    let reasoningText = data.reasoning || "Analyzing query and planning research strategy";
                    if (data.content) {
                      reasoningText = data.content.replace(/^[💭🔍📊🔧✍️Reasoning:\s]*/g, "").trim();
                    }
                    if (reasoningText.length > 100) {
                      reasoningText = reasoningText.slice(0, 100) + "...";
                    }
                    thinkingMessages.push(`Step ${stepNum}: Planning - ${reasoningText}`);
                    // Don't overwrite status - let tool progress messages show
                  } else if (nodeName === "tool_executor") {
                    const toolCall = data.tool_call;
                    if (toolCall) {
                      const toolName = toolCall.name;
                      const args = toolCall.arguments || {};
                      const argStr = args.query || args.url || args.industry || Object.values(args)[0] || "";
                      const shortArg = typeof argStr === 'string' ? argStr.slice(0, 40) : String(argStr).slice(0, 40);
                      thinkingMessages.push(`Step ${stepNum}: Running ${toolName}("${shortArg}")`);
                      // Show tool start, then let progress messages update it
                      setSessionThinking(`Starting ${toolName} (Step ${stepNum})`, activeSessionId || undefined);
                    } else {
                      thinkingMessages.push(`Step ${stepNum}: Executing tool`);
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
                    setSessionThinking(`Validating research data (Step ${stepNum})`, activeSessionId || undefined);
                  } else if (nodeName === "response") {
                    thinkingMessages.push(`Step ${stepNum}: Generating final response`);
                    setSessionThinking(`Generating comprehensive report - please wait (Step ${stepNum})`, activeSessionId || undefined);
                  }

                  // Log for debugging
                  if (data.content) {
                    console.log(`📝 Received content from ${nodeName}: ${data.content.substring(0, 100)}...`);
                  }
                  
                  // Accept content if it's valid and not an internal thinking message
                  // Skip short status messages - real reports are > 500 chars
                  const isInternalMessage = (data.content?.startsWith("Reasoning:") && nodeName !== "response") ||
                                            (nodeName === "reflection" && data.content?.length < 500) ||
                                            data.content?.startsWith("Found ") ||
                                            data.content?.startsWith("Searching ");
                  
                  if (data.content && data.content.trim() && !isInternalMessage) {
                    assistantContent = data.content;
                    console.log(`✅ Set assistantContent (${assistantContent.length} chars)`);
                    
                    setSessions((prevSessions) => {
                      return prevSessions.map((session) => {
                        if (session.id !== activeSessionId) return session;
                        
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
                } else if (data.type === "final_response" && data.content) {
                  // CRITICAL: Handle explicit final response event
                  // This ensures we always display the full report
                  console.log(`📥 RECEIVED FINAL RESPONSE: ${data.content.length} chars`);
                  assistantContent = data.content;
                  
                  setSessions((prevSessions) => {
                    return prevSessions.map((session) => {
                      if (session.id !== activeSessionId) return session;
                      
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
                } else if (data.type === "clarification_stream" && data.content) {
                  // Handle streaming clarification content - progressive updates
                  assistantContent = data.content;
                  
                  setSessions((prevSessions) => {
                    return prevSessions.map((session) => {
                      if (session.id !== activeSessionId) return session;
                      
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
                                isStreaming: true  // Still streaming
                              }
                            : msg
                        );
                      } else {
                        const newMessage: Message = {
                          id: assistantMessageId,
                          role: "assistant" as const,
                          content: assistantContent,
                          timestamp: new Date().toISOString(),
                          isStreaming: true,  // Still streaming
                          thinkingSteps: [...thinkingMessages],
                        };
                        updatedMessages = [...currentMessages, newMessage];
                      }
                      
                      return { ...session, messages: updatedMessages };
                    });
                  });
                } else if (data.type === "clarification" && data.content) {
                  // Handle final clarification content (streaming complete)
                  console.log(`📥 RECEIVED CLARIFICATION COMPLETE: ${data.content.length} chars`);
                  assistantContent = data.content;
                  
                  setSessions((prevSessions) => {
                    return prevSessions.map((session) => {
                      if (session.id !== activeSessionId) return session;
                      
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
                                isStreaming: false  // Streaming complete
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
                } else if (data.type === "complete") {
                  setSessionThinking(null, activeSessionId || undefined);
                  if (activeSessionId) {
                    generateSessionTitle(activeSessionId, content).catch(console.error);
                  }
                } else if (data.type === "error") {
                  throw new Error(data.message || "Unknown error");
                }
              } catch (e: any) {
                // Log parse errors for debugging (common with chunked data)
                console.warn(`SSE parse warning: ${e.message}`, line.slice(0, 100));
                if (e.message && e.message.includes("Error")) {
                  throw e;
                }
              }
            }
          }
        }
      }
      
      // Process any remaining data in buffer after stream ends
      if (sseBuffer.trim()) {
        const remainingLines = sseBuffer.split("\n");
        for (const line of remainingLines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "final_response" && data.content) {
                console.log(`📥 RECEIVED FINAL RESPONSE (from buffer): ${data.content.length} chars`);
                assistantContent = data.content;
              }
            } catch (e) {
              console.warn("Failed to parse remaining buffer:", e);
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

  // Initialize - fetch sessions from backend API
  useEffect(() => {
    const initializeSessions = async () => {
      try {
        // Try to load from backend API first
        const dbSessions = await fetchSessions();
        
        if (dbSessions.length > 0) {
          console.log(`📂 Loaded ${dbSessions.length} sessions from database`);
          setSessions(dbSessions);
          setCurrentSessionId(dbSessions[0].id);
          
          // Load messages for the first session
          const details = await fetchSessionDetails(dbSessions[0].id);
          if (details) {
            setSessions((prev) =>
              prev.map((s) =>
                s.id === dbSessions[0].id ? { ...s, messages: details.messages } : s
              )
            );
          }
          
          setIsInitialized(true);
          return;
        }
      } catch (error) {
        console.warn("Failed to load sessions from API:", error);
      }
      
      // Fallback: Create initial session if none exist
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
    };
    
    initializeSessions();
  }, [fetchSessions, fetchSessionDetails]);

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
