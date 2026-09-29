import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Sparkles } from "lucide-react";
import { ChatMessage } from "@/lib/types";
import { cn } from "./ui/Button";

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn(
      "flex w-full mb-6 animate-slide-up",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "flex max-w-[85%] sm:max-w-[75%]",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1",
          isUser ? "ml-3 bg-primary" : "mr-3 bg-surface border border-surface-border",
        )}>
          {isUser ? <User className="w-5 h-5 text-white" /> : <Sparkles className="w-5 h-5 text-primary" />}
        </div>

        <div className={cn(
          "px-5 py-4 rounded-2xl",
          isUser ? "bg-primary text-white rounded-tr-sm" : "glass-panel rounded-tl-sm"
        )}>
          
          <div className={cn(
            "prose prose-sm max-w-none leading-relaxed",
            isUser ? "prose-invert text-white" : "prose-invert"
          )}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            
            {isStreaming && (
              <span className="inline-flex space-x-1 ml-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse-dot" style={{ animationDelay: "0ms" }}/>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse-dot" style={{ animationDelay: "200ms" }}/>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse-dot" style={{ animationDelay: "400ms" }}/>
              </span>
            )}
          </div>

          {message.citations && message.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-white/10">
              <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wider">Sources</p>
              <div className="flex flex-wrap gap-2">
                {message.citations.map((cite, idx) => (
                  <div key={idx} className="group relative">
                    <span className="inline-flex items-center px-2 py-1 rounded bg-white/5 border border-white/10 text-xs text-gray-300 cursor-help hover:bg-white/10 transition-colors">
                      Page {cite.pageNumber}
                    </span>
                    
                    <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 text-xs">
                      {cite.sectionTitle && <p className="font-bold text-white mb-1">{cite.sectionTitle}</p>}
                      <p className="text-gray-300 italic line-clamp-4">&quot;{cite.snippet}&quot;</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
