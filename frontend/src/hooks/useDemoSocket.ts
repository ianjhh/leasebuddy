import { useRef, useCallback, useEffect } from "react";
import { WebSocketMessage } from "@/lib/types";
import { findDemoAnswer } from "@/lib/demo";

const THINKING_MS = 900;
const TOKEN_MS = 28;

// Stands in for useWebSocket in the static demo: same interface, but it
// replays a recorded answer as a token stream instead of calling the agent.
export function useDemoSocket(leaseId: string | null) {
  const messageHandlerRef = useRef<(msg: WebSocketMessage) => void>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const onMessage = useCallback((handler: (msg: WebSocketMessage) => void) => {
    messageHandlerRef.current = handler;
  }, []);

  const sendMessage = useCallback((query: string) => {
    const emit = (msg: WebSocketMessage, delay: number) => {
      timersRef.current.push(setTimeout(() => messageHandlerRef.current?.(msg), delay));
    };

    const recorded = findDemoAnswer(query);
    if (!recorded) {
      emit({
        type: "token",
        content: "This demo can only replay answers the agent gave during evaluation, so it can't answer new questions. Try one of the suggested questions, or run LeaseBuddy locally to ask anything.",
      }, THINKING_MS);
      emit({ type: "done" }, THINKING_MS);
      return;
    }

    // Split into words, keeping the whitespace, so markdown renders as it streams.
    const tokens = recorded.answer.match(/\S+\s*/g) ?? [recorded.answer];
    tokens.forEach((token, i) => emit({ type: "token", content: token }, THINKING_MS + i * TOKEN_MS));

    const end = THINKING_MS + tokens.length * TOKEN_MS;
    const passes = recorded.retrievalPasses === 1 ? "1 retrieval pass" : `${recorded.retrievalPasses} retrieval passes`;
    if (recorded.citations.length > 0) emit({ type: "citations", data: recorded.citations }, end);
    emit({ type: "note", content: `Recorded answer · the agent took ${recorded.latencySeconds.toFixed(1)}s running locally, ${passes}` }, end);
    emit({ type: "done" }, end);
  }, []);

  useEffect(() => {
    const timers = timersRef.current;
    return () => timers.forEach(clearTimeout);
  }, []);

  return {
    connectionState: leaseId ? ("connected" as const) : ("disconnected" as const),
    sendMessage,
    onMessage,
  };
}
