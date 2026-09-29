"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, FileText, Search } from "lucide-react";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { useLeaseUpload } from "@/hooks/useLeaseUpload";

export default function Home() {
  const router = useRouter(); 
  const { uploadFile, status, progress, errorMsg, readyLeaseId } = useLeaseUpload();

  useEffect(() => {
    if (status === "completed" && readyLeaseId) {
      setTimeout(() => {
        router.push(`/chat/${readyLeaseId}`);
      }, 1000);
    }
  }, [status, readyLeaseId, router]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[128px] -z-10" />

      <div className="w-full max-w-4xl mx-auto text-center mb-12 animate-slide-up">
        <div className="inline-flex items-center justify-center p-2 bg-primary/10 rounded-2xl mb-6">
          <Sparkles className="w-6 h-6 text-primary" />
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight">
          Understand your lease in <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-400">seconds.</span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Upload your residential lease agreement and ask questions in plain English. No legal degree required.
        </p>
      </div>

      <div className="w-full max-w-3xl mx-auto animate-fade-in" style={{ animationDelay: "200ms" }}>
        {status === "idle" || status === "error" || status === "uploading" ? (
          <FileUpload onUpload={uploadFile} isLoading={status === "uploading"} />
        ) : (
          <ProcessingStatus status={status} progress={progress} />
        )}

        {status === "error" && errorMsg && (
          <p className="text-red-400 text-center mt-4">{errorMsg}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-4xl mx-auto opacity-70">
        <div className="flex flex-col items-center text-center">
          <FileText className="w-8 h-8 text-gray-400 mb-3" />
          <h3 className="font-semibold mb-1">Instant Analysis</h3>
          <p className="text-sm text-gray-500">We extract every clause and condition securely.</p>
        </div>
        <div className="flex flex-col items-center text-center">
          <Search className="w-8 h-8 text-gray-400 mb-3" />
          <h3 className="font-semibold mb-1">Smart Citations</h3>
          <p className="text-sm text-gray-500">Answers include exact page numbers and quotes.</p>
        </div>
        <div className="flex flex-col items-center text-center">
          <Sparkles className="w-8 h-8 text-gray-400 mb-3" />
          <h3 className="font-semibold mb-1">AI Powered</h3>
          <p className="text-sm text-gray-500">Powered by advanced RAG and Large Language Models.</p>
        </div>
      </div>
    </main>
  );
}
