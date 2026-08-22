"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, AlertCircle, Sparkles } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { getLease } from "@/lib/api";
import { Lease } from "@/lib/types";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { Button } from "@/components/ui/Button";

export default function ChatPage() {
  const params = useParams(); 
  const router = useRouter();
  const leaseId = params.leaseId as string;
  
  const [isMounted, setIsMounted] = useState(false);
  const [lease, setLease] = useState<Lease | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { messages, isStreaming, sendQuery, connectionState } = useChat(leaseId);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
                {connectionState}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[50vh] text-center animate-fade-in opacity-50">
              <Sparkles className="w-12 h-12 text-gray-500 mb-4" />
              <h2 className="text-xl font-semibold mb-2">Ask about your lease</h2>
              <p className="text-sm text-gray-400 mb-8 max-w-md">
                Try asking about pets, breaking the lease early, or maintenance responsibilities.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                {["Are pets allowed?", "What is the penalty for breaking the lease early?", "Who is responsible for lawn care?", "When is rent due?"].map((q, i) => (
                  <button 
                    key={i}
                    onClick={() => sendQuery(q)}
                    className="p-3 text-sm text-left bg-surface border border-surface-border rounded-xl hover:bg-white/5 transition-colors"
                  >
                    &quot;{q}&quot;
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="pb-4">
              {messages.map((msg, index) => (
                <MessageBubble 
                  key={msg.id} 
                  message={msg} 
                  isStreaming={isStreaming && index === messages.length - 1 && msg.role === "assistant"}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      <div className="p-4 sm:p-6 bg-gradient-to-t from-background via-background to-transparent pt-10 z-10">
        <div className="max-w-3xl mx-auto">
          <ChatInput 
            onSend={sendQuery} 
            disabled={isStreaming || connectionState !== "connected"} 
          />
          <p className="text-center text-xs text-gray-500 mt-3">
            AI can make mistakes. Always verify important legal details in the original document.
          </p>
        </div>
      </div>

    </div>
  );
}
