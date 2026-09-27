import { useState, useCallback, useEffect } from "react";
import { ChatMessage } from "@/lib/types";
import { DEMO_LEASE, IS_DEMO } from "@/lib/demo";
import { useWebSocket } from "./useWebSocket";
import { useDemoSocket } from "./useDemoSocket";

// Only called from event handlers, never during render.
const generateId = () => Math.random().toString(36).substring(2, 9);

// Fixed at build time, so the same hook runs on every render.
const useSocket = IS_DEMO ? useDemoSocket : useWebSocket;

export function useChat(leaseId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [{
    id: "greeting",
    role: "assistant",
    content: IS_DEMO
      ? `Hi there! 👋 This is a sample ${DEMO_LEASE.pageCount}-page lease. Pick a question below to see how I answer, with the page I found it on.`
      : "Hi there! 👋 Ask me anything about the document you just uploaded!",
    createdAt: new Date().toISOString(),
  }]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  
  const { connectionState, sendMessage, onMessage } = useSocket(leaseId);

  useEffect(() => {
    onMessage((msg) => {
      if (msg.type === "token") {
        setIsThinking(false);
        setIsStreaming(true);
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          
          if (!lastMsg || lastMsg.role !== "assistant") {
            const newAssistantMsg: ChatMessage = {
              id: generateId(),
              role: "assistant",
              content: msg.content,
              createdAt: new Date().toISOString(),
            };
            return [...prev, newAssistantMsg];
          }

          const updatedMsg = {
            ...lastMsg,
            content: lastMsg.content + msg.content,
          };
          
          return [...prev.slice(0, -1), updatedMsg];
        });
      } 
      else if (msg.type === "citations") {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (!lastMsg || lastMsg.role !== "assistant") return prev;

          const updatedMsg = {
            ...lastMsg,
            citations: msg.data,
          };
          return [...prev.slice(0, -1), updatedMsg];
        });
      }
      else if (msg.type === "note") {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (!lastMsg || lastMsg.role !== "assistant") return prev;
          return [...prev.slice(0, -1), { ...lastMsg, note: msg.content }];
        });
      }
      else if (msg.type === "done") {
        setIsStreaming(false);
        setIsThinking(false);
      } 
      else if (msg.type === "error") {
        setIsStreaming(false);
        setIsThinking(false);
        const errorMsg: ChatMessage = {
          id: generateId(),
          role: "assistant",
          content: `*Error:* ${msg.message}`,
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    });
  }, [onMessage]);

  const sendQuery = useCallback((query: string) => {
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content: query,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    sendMessage(query);
    setIsThinking(true);
  }, [sendMessage]);

  return {
    messages,
    isStreaming,
    isThinking,
    connectionState,
    sendQuery,
  };
}
