"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, AlertCircle } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { getLease } from "@/lib/api";
import { DEMO_SUGGESTED, IS_DEMO } from "@/lib/demo";
import { Lease } from "@/lib/types";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { Button } from "@/components/ui/Button";

// Nothing to subscribe to: the value only differs between server and client.
const subscribeToNothing = () => () => {};

export function ChatView() {
  const params = useParams(); 
  const router = useRouter();
  const leaseId = params.leaseId as string;
  
  // false while rendering on the server, true in the browser, so the page
  // renders nothing until hydration and avoids a mismatch.
  const isMounted = useSyncExternalStore(subscribeToNothing, () => true, () => false);
  const [lease, setLease] = useState<Lease | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { messages, isStreaming, isThinking, sendQuery, connectionState } = useChat(leaseId);
  
  const logRef = useRef<HTMLDivElement>(null);
  const asked = new Set(messages.filter((m) => m.role === "user").map((m) => m.content));

  useEffect(() => {
    async function loadLease() {
      try {
        const data = await getLease(leaseId);
        if (data.status !== "completed") {
          setError("This document is not ready yet.");
        } else {
          setLease(data);
        }
      } catch {
        setError("Document not found.");
      }
    }
    loadLease();
  }, [leaseId]);

  // Keep the newest message in view by scrolling the message list itself.
  // scrollIntoView would also scroll any page this app is embedded in.
  useEffect(() => {
    const log = logRef.current;
    log?.scrollTo({ top: log.scrollHeight, behavior: "smooth" });
  }, [messages, isStreaming]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-panel p-8 rounded-2xl text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Error</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <Button onClick={() => router.push("/")}>Go Home</Button>
        </div>
      </div>
    );
  }

  if (!isMounted) return null;

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      
      <header className="glass-panel rounded-none border-t-0 border-x-0 border-b z-10 flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => router.push("/")}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-primary" />
              <h1 className="font-semibold text-sm">
                {lease ? lease.filename : "Loading..."}
              </h1>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <div className={`w-2 h-2 rounded-full ${
                connectionState === "connected" ? "bg-green-500" : 
                connectionState === "connecting" ? "bg-yellow-500 animate-pulse" : "bg-red-500"
              }`} />
              <span className="text-xs text-gray-400 uppercase tracking-wider">
                {IS_DEMO ? "demo · recorded answers" : connectionState}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div ref={logRef} className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth">
        <div className="max-w-3xl mx-auto">
          <div className="pb-4">
              {messages.map((msg, index) => (
                <MessageBubble 
                  key={msg.id} 
                  message={msg} 
                  isStreaming={isStreaming && index === messages.length - 1 && msg.role === "assistant"}
                />
              ))}
              {isThinking && (
                <div className="flex justify-start w-full mt-4 animate-pulse">
                  <div className="bg-surface rounded-2xl rounded-tl-sm px-5 py-4 max-w-[85%] border border-surface-border">
                    <div className="flex space-x-2 items-center h-4">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    </div>
                  </div>
                </div>
              )}
              <div className="h-4" />
            </div>
        </div>
      </div>

      <div className="p-4 sm:p-6 bg-gradient-to-t from-background via-background to-transparent pt-10 z-10">
        <div className="max-w-3xl mx-auto">
          {IS_DEMO && (
            <div className="flex flex-wrap gap-2 pb-3 mb-1">
              {DEMO_SUGGESTED.filter((q) => !asked.has(q)).map((q) => (
                <button
                  key={q}
                  onClick={() => sendQuery(q)}
                  disabled={isStreaming || isThinking}
                  className="flex-shrink-0 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-xs text-gray-300 transition-colors hover:bg-primary/20 hover:border-primary/40 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          <ChatInput
            onSend={sendQuery} 
            disabled={isStreaming || isThinking || connectionState !== "connected"} 
          />
          <p className="text-center text-xs text-gray-500 mt-3">
            AI can make mistakes. Always verify important legal details in the original document.
          </p>
        </div>
      </div>

    </div>
  );
}
