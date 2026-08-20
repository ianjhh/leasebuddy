import { useState, useCallback } from "react";
import { uploadLease, getLease } from "@/lib/api";

type UploadStatus = "idle" | "uploading" | "processing" | "completed" | "error";

export function useLeaseUpload() {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0); 
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [readyLeaseId, setReadyLeaseId] = useState<string | null>(null);

  const pollProcessingStatus = async (leaseId: string) => {
    setStatus("processing");
    let fauxProgress = 50;
    
    const pollInterval = setInterval(async () => {
      try {
        const leaseData = await getLease(leaseId);
        
        if (leaseData.status === "completed") {
          clearInterval(pollInterval);
          setProgress(100);
          setStatus("completed");
          setReadyLeaseId(leaseId);
        } else if (leaseData.status === "error") {
          clearInterval(pollInterval);
          setStatus("error");
          setErrorMsg("Failed to process document.");
        } else {
          if (fauxProgress < 95) {
            fauxProgress += 5;
            setProgress(fauxProgress);
          }
        }
      } catch {
        clearInterval(pollInterval);
        setStatus("error");
        setErrorMsg("Lost connection while checking status.");
      }
    }, 2000); 
  };

  const uploadFile = useCallback(async (file: File) => {
    setStatus("uploading");
    setProgress(20); 
    setErrorMsg(null);

    try {
      const response = await uploadLease(file);
      setProgress(50); 
      
      pollProcessingStatus(response.lease_id);
      
    } catch (e: unknown) {
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "An error occurred during upload.");
    }
  }, []);

  return {
    uploadFile,
    status,
    progress,
    errorMsg,
    readyLeaseId,
  };
}
