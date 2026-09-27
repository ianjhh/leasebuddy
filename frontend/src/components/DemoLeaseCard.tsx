import React from "react";
import { FileText, ArrowRight } from "lucide-react";
import { DEMO_LEASE } from "@/lib/demo";

interface DemoLeaseCardProps {
  onOpen: () => void;
}

// Replaces the upload box in the static demo, which has no backend to process uploads.
export function DemoLeaseCard({ onOpen }: DemoLeaseCardProps) {
  return (
    <div className="w-full max-w-xl mx-auto">
      <button
        onClick={onOpen}
        className="group w-full glass-panel rounded-2xl p-6 flex items-center gap-4 text-left transition-all hover:border-primary/50 hover:shadow-[0_0_40px_-12px] hover:shadow-primary/60"
      >
        <div className="p-3 bg-primary/20 rounded-lg text-primary flex-shrink-0">
          <FileText className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold">Open the sample lease</p>
          <p className="text-sm text-gray-400 truncate">
            {DEMO_LEASE.filename} · {DEMO_LEASE.pageCount} pages
          </p>
        </div>
        <ArrowRight className="w-5 h-5 text-gray-400 transition-transform group-hover:translate-x-1 group-hover:text-white" />
      </button>
      <p className="text-center text-xs text-gray-500 mt-4 leading-relaxed">
        Demo: the AI models run locally, so this version replays answers the real agent
        gave on a synthetic lease during evaluation.
      </p>
    </div>
  );
}
