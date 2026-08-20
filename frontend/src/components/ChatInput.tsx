import React, { useState, useRef, useEffect } from "react";
import { SendHorizontal } from "lucide-react";
import { cn } from "./ui/Button";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "inherit";
      const height = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(height, 96)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-2 flex items-end relative border-gray-700 shadow-2xl">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Please wait..." : "Ask about your lease..."}
        disabled={disabled}
        className="w-full max-h-32 bg-transparent text-white placeholder-gray-500 resize-none outline-none py-3 px-4 rounded-xl text-sm"
        rows={1}
      />
      <button
        onClick={handleSend}
        disabled={!text.trim() || disabled}
        className={cn(
          "mb-1 mr-1 p-2 rounded-xl transition-all duration-200 flex-shrink-0 flex items-center justify-center",
          text.trim() && !disabled 
            ? "bg-primary text-white shadow-lg hover:bg-primary-hover" 
            : "bg-surface text-gray-500 cursor-not-allowed"
        )}
      >
        <SendHorizontal className="w-5 h-5" />
      </button>
    </div>
  );
}
