import { useState, useEffect, useRef, useCallback } from "react";
import { WebSocketMessage } from "@/lib/types";

const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api")
  .replace(/^http/, "ws")
  .replace(/\/api$/, "");

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket(leaseId: string | null) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const messageHandlerRef = useRef<(msg: WebSocketMessage) => void>(null);

  const onMessage = useCallback((handler: (msg: WebSocketMessage) => void) => {
    messageHandlerRef.current = handler;
  }, []);

  const sendMessage = useCallback((query: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "query", content: query }));
    } else {
      console.error("WebSocket is not connected");
    }
  }, []);

  const connect = useCallback(function connect() {
    if (!leaseId) return;

    setConnectionState("connecting");
    
    const ws = new WebSocket(`${WS_BASE_URL}/ws/chat/${leaseId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected!");
      setConnectionState("connected");
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        if (messageHandlerRef.current) {
          messageHandlerRef.current(data);
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message", e);
      }
    };

    ws.onclose = () => {
      setConnectionState("disconnected");
      
      const attempts = reconnectAttemptsRef.current;
      const backoffMs = Math.min(1000 * Math.pow(2, attempts), 30000);
      
      console.log(`WebSocket closed. Reconnecting in ${backoffMs}ms...`);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current += 1;
        connect();
      }, backoffMs);
    };

    ws.onerror = () => {
      console.error("WebSocket error occurred");
    };
  }, [leaseId]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; 
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    connectionState,
    sendMessage,
    onMessage
  };
}
