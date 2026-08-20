import { useState, useCallback, useEffect } from "react";
import { ChatMessage } from "@/lib/types";
import { useWebSocket } from "./useWebSocket";

export function useChat(leaseId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const { connectionState, sendMessage, onMessage } = useWebSocket(leaseId);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  useEffect(() => {
    onMessage((msg) => {
      if (msg.type === "token") {
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
      else if (msg.type === "done") {
        setIsStreaming(false);
      } 
      else if (msg.type === "error") {
        setIsStreaming(false);
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
  }, [sendMessage]);

  return {
    messages,
    isStreaming,
    connectionState,
    sendQuery,
  };
}
