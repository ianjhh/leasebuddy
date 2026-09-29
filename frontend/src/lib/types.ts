export interface Lease {
  id: string;
  filename: string;
  status: "processing" | "completed" | "error";
  pageCount: number;
  createdAt: string;
}

export interface Citation {
  chunkId: string;
  pageNumber: number;
  sectionTitle?: string;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  createdAt: string;
}

export type WebSocketMessage = 
  | { type: "token"; content: string }
  | { type: "citations"; data: Citation[] }
  | { type: "done" }
  | { type: "error"; message: string };

export interface UploadResponse {
  lease_id: string;
  message: string;
}
