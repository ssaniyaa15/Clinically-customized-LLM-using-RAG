"use client";

import { useCallback, useEffect, useState } from "react";

import {
  type ChatMessage,
  getSession,
  getStoredSessionId,
  sendMessage,
  setStoredSessionId,
  type UrgencyLevel,
} from "@/lib/chat-api";

export interface ChatUiMessage extends ChatMessage {
  urgencyLevel?: UrgencyLevel;
  suggestedActions?: string[];
  disclaimer?: string;
}

interface UseChatState {
  messages: ChatUiMessage[];
  sessionId: string | null;
  isLoading: boolean;
  urgencyLevel: UrgencyLevel;
  error: string | null;
  sendMessage: (text: string) => Promise<void>;
  dismissEmergencyBanner: () => void;
}

export function useChat(patientId: string): UseChatState {
  const [messages, setMessages] = useState<ChatUiMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [urgencyLevel, setUrgencyLevel] = useState<UrgencyLevel>("normal");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = getStoredSessionId(patientId);
    if (!stored) return;
    setSessionId(stored);
    void getSession(stored)
      .then((session) => {
        setMessages(session.messages as ChatUiMessage[]);
      })
      .catch(() => {
        setError("Unable to restore previous chat session.");
      });
  }, [patientId]);

  const send = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      setError(null);
      setUrgencyLevel("normal");
      const userMessage: ChatUiMessage = {
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      try {
        const response = await sendMessage(patientId, sessionId, text);
        if (!sessionId || sessionId !== response.session_id) {
          setSessionId(response.session_id);
          setStoredSessionId(patientId, response.session_id);
        }
        setUrgencyLevel(response.urgency_level);
        const assistantMessage: ChatUiMessage = {
          role: "assistant",
          content: response.reply,
          timestamp: new Date().toISOString(),
          urgencyLevel: response.urgency_level,
          suggestedActions: response.suggested_actions,
          disclaimer: response.disclaimer,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message.");
      } finally {
        setIsLoading(false);
      }
    },
    [patientId, sessionId],
  );

  const dismissEmergencyBanner = useCallback(() => {
    setUrgencyLevel("normal");
  }, []);

  return {
    messages,
    sessionId,
    isLoading,
    urgencyLevel,
    error,
    sendMessage: send,
    dismissEmergencyBanner,
  };
}

