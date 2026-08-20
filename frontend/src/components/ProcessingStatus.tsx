import React from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { cn } from "./ui/Button";

interface ProcessingStatusProps {
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  progress: number;
}

export function ProcessingStatus({ status, progress }: ProcessingStatusProps) {
  const steps = [
    { label: "Uploading file", done: progress >= 50 },
    { label: "Extracting text & images", done: progress >= 75 },
    { label: "Generating embeddings", done: status === "completed" },
  ];

  return (
    <div className="glass-panel p-8 rounded-2xl w-full max-w-xl mx-auto animate-fade-in shadow-2xl">
      <div className="text-center mb-8">
        <h3 className="text-xl font-bold mb-2">Processing Document</h3>
        <p className="text-gray-400 text-sm">Our AI is reading your lease. This usually takes about 10-20 seconds.</p>
      </div>

      <div className="w-full bg-surface border border-surface-border rounded-full h-2 mb-8 overflow-hidden">
        <div 
          className="bg-primary h-2 rounded-full transition-all duration-500 ease-out" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => {
          const isCurrent = !step.done && (index === 0 || steps[index - 1].done);
          
          return (
            <div key={index} className="flex items-center space-x-3">
              {step.done ? (
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              ) : isCurrent && status !== "error" ? (
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-surface-border" />
              )}
              
              <span className={cn(
                "text-sm font-medium transition-colors duration-300",
                step.done ? "text-gray-300" : isCurrent ? "text-white" : "text-gray-500"
              )}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
