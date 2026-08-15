# Chapter 10: Building the Frontend (Next.js + TypeScript + TailwindCSS)

Welcome to Part 4 of the LeaseGPT tutorial! By now, you have a fully functioning backend that can process PDFs, extract text, and answer questions using AI. But it's just a backend — it doesn't have a user interface (UI) yet. 

In this chapter, we are going to build a **STUNNING, premium, dark-themed frontend** for LeaseGPT. It will look similar to modern AI chat interfaces like ChatGPT or Perplexity, complete with glassmorphism effects (that cool, frosted-glass look), smooth animations, and a seamless chat experience.

Before we write code, let's break down the technologies we'll be using. Think of building a website like building a house:
- **HTML** is the structure (walls, floors, roof).
- **CSS** is the design (paint, wallpaper, furniture).
- **JavaScript** is the electricity and plumbing (making things light up and flush).

For our modern app, we'll use tools that make building this house much faster and stronger:

1. **Next.js (The Blueprint & Foundation)**: Next.js is a "framework" built on top of React. If plain React is like buying wood and nails to build a house, Next.js is like buying a prefabricated house where the plumbing, routing (moving between rooms/pages), and server features are already built-in. It uses the **App Router**, meaning we create pages just by making folders!
2. **TypeScript (The Building Inspector)**: TypeScript is JavaScript with "types." Imagine you have moving boxes. In regular JavaScript, a box is just a box. You can put clothes in it, take them out, and put dishes in it. If you forget and throw the box, the dishes break. In TypeScript, you label the box "Clothes Only." If you try to put dishes in, TypeScript yells at you *before* you seal the box. It catches bugs before you run the code!
3. **TailwindCSS (The Instant Paint & Decorator)**: Instead of writing separate CSS files (which can get messy), Tailwind is a "utility-first" CSS framework. You apply styles directly to your HTML elements using class names. For example, `className="bg-blue-500 text-white p-4 rounded-lg"` means "blue background, white text, padding of size 4, rounded corners." It's like having a catalog of pre-mixed paints you can just slap onto walls instantly.
4. **React Hooks (The Smart Appliances)**: Hooks are special functions in React that let your components "hook into" React features. For example, `useState` lets a component remember things (like if a button was clicked), and `useEffect` lets a component do things automatically (like fetching data when the page loads). **Custom Hooks** are hooks we write ourselves to bundle up complex logic so we can reuse it easily.

Let's dive in!

---

## 10.1: Initialize the Next.js Project

First, we need to create our frontend project. Open a new terminal window in your project's root folder.

> [!IMPORTANT]
> Make sure you are in the main `leasegpt` folder (the parent folder of your backend) before running this command.

Run this exact command:

```powershell
# Create a new Next.js app in a folder named 'frontend'
npx -y create-next-app@latest ./frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
```

### What just happened?
Let's break down that command:
- `npx create-next-app@latest`: This downloads and runs the Next.js setup wizard.
- `./frontend`: This tells it to create the app inside a folder called `frontend`.
- `--typescript`: We want to use TypeScript (our building inspector).
- `--tailwind`: We want TailwindCSS pre-configured.
- `--eslint`: Adds a tool that checks our code for formatting errors.
- `--app`: Uses the modern Next.js 14+ "App Router" (where folders define URL paths).
- `--src-dir`: Puts all our code inside a `src` folder (keeps things neat).
- `--import-alias "@/*"`: A shortcut! Instead of writing `../../../components/Button`, we can just write `@/components/Button`.
- `--use-npm`: Uses npm as our package manager.

Once it finishes, open the `frontend` folder in your code editor. Your folder structure will look roughly like this:
```
frontend/
├── src/
│   ├── app/           # Where our pages live
│   │   ├── layout.tsx # The main wrapper for all pages
│   │   ├── page.tsx   # The home page (localhost:3000/)
│   │   └── globals.css# Global styles
├── public/            # Static files like images or icons
├── tailwind.config.ts # Tailwind customization
├── package.json       # List of installed packages
└── tsconfig.json      # TypeScript settings
```

---

## 10.2: Configure TailwindCSS Theme

We want LeaseGPT to look *premium*. Let's set up a dark theme with glassmorphism and smooth animations.

First, let's install some helpful icons. We'll use `lucide-react`, a popular icon library.

```powershell
cd frontend
npm install lucide-react clsx tailwind-merge framer-motion react-markdown remark-gfm
```
*(We also installed `clsx` and `tailwind-merge` to help us combine Tailwind classes neatly, `framer-motion` for animations, and `react-markdown` to render the AI's responses beautifully.)*

Open `tailwind.config.ts` and replace its entire contents with this:

```typescript
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  // Tell Tailwind to look for classes in these files
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // We are adding custom colors for our dark theme
      colors: {
        background: "#0f1115", // Deep dark slate background
        foreground: "#f8fafc", // Off-white text
        primary: {
          DEFAULT: "#6366f1", // Indigo accent
          hover: "#4f46e5",
        },
        surface: {
          DEFAULT: "rgba(30, 41, 59, 0.7)", // Semi-transparent slate for glass effect
          border: "rgba(148, 163, 184, 0.1)", // Very faint border
        }
      },
      // Custom animations!
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "0.4", transform: "scale(0.8)" },
          "50%": { opacity: "1", transform: "scale(1.2)" },
        }
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out forwards",
        "slide-up": "slide-up 0.4s ease-out forwards",
        "pulse-dot": "pulse-dot 1.5s infinite ease-in-out",
      }
    },
  },
  plugins: [],
};

export default config;
```

Next, open `src/app/globals.css` and replace it entirely with:

```css
/* frontend/src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: dark;
}

body {
  background-color: theme('colors.background');
  color: theme('colors.foreground');
  /* The Inter font looks very clean and modern */
  font-family: var(--font-inter), sans-serif;
}

/* Custom scrollbar for a polished look */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}

/* A utility class for our glassmorphism effect */
.glass-panel {
  background: theme('colors.surface.DEFAULT');
  backdrop-filter: blur(12px); /* This makes what's behind it blurry! */
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid theme('colors.surface.border');
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}
```

### What just happened?
We set up our design system! We told Tailwind to use a specific very dark background color (`#0f1115`), created some custom animations for sliding elements onto the screen, and created a `.glass-panel` CSS class that uses `backdrop-filter: blur()` to create a frosted glass effect that looks incredibly premium.

---

## 10.3: TypeScript Types

Before we build components, we need to define our data types. Remember, TypeScript is our "Building Inspector" making sure our data boxes are labeled correctly.

Create a new file `src/lib/types.ts`:
*(Note: You might need to create the `lib` folder inside `src` first)*

```typescript
// frontend/src/lib/types.ts

/**
 * Represents a Lease document in our system.
 * This must match what our FastAPI backend returns!
 */
export interface Lease {
  id: string;             // A unique ID, e.g. a UUID
  filename: string;       // Original name, e.g., "apartment_lease.pdf"
  status: "processing" | "ready" | "error"; // Current state
  pageCount: number;      // How many pages in the PDF
  createdAt: string;      // ISO Date string
}

/**
 * Represents a snippet of text cited by the AI to prove its answer.
 */
export interface Citation {
  chunkId: string;        // ID of the text chunk in our vector database
  pageNumber: number;     // Which page of the lease it's on
  sectionTitle?: string;  // Optional title, e.g., "7. Utilities"
  snippet: string;        // The actual text from the lease
}

/**
 * Represents a single message in the chat window.
 */
export interface ChatMessage {
  id: string;             // Unique ID for the message
  role: "user" | "assistant"; // Who sent it?
  content: string;        // The text of the message
  citations?: Citation[]; // If assistant, it might have citations
  createdAt: string;      // ISO Date string
}

/**
 * These are the different types of messages our WebSocket can send us.
 * This is called a "Discriminated Union" in TypeScript.
 * It means the object can be ONE of these shapes, determined by the 'type' field.
 */
export type WebSocketMessage = 
  | { type: "token"; content: string } // A piece of the AI's answer
  | { type: "citations"; data: Citation[] } // References
  | { type: "done" } // AI finished typing
  | { type: "error"; message: string }; // Something broke

/**
 * What the backend returns when we successfully upload a file
 */
export interface UploadResponse {
  lease_id: string;
  message: string;
}
```

### What just happened?
We defined the shapes of our data using `interface` and `type`. 
A **Discriminated Union** (like `WebSocketMessage`) is a fantastic TypeScript feature. It says: "If the `type` is 'token', then I guarantee this object has a `content` string. But if `type` is 'error', it will have a `message` string instead." This prevents us from accidentally trying to read `content` on an error message!

---

## 10.4: API Client

We need a way to talk to our FastAPI backend for standard HTTP requests (uploading files, getting lease status).

Create `src/lib/api.ts`:

```typescript
// frontend/src/lib/api.ts
import { Lease, UploadResponse } from "./types";

// Get the backend URL from our environment variables, default to localhost:8000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * Uploads a lease file (PDF or Image) to the backend.
 * @param file The file selected by the user
 * @returns An UploadResponse containing the new leaseId
 */
export async function uploadLease(file: File): Promise<UploadResponse> {
  // 1. Create a FormData object (this is how you send files in JavaScript)
  const formData = new FormData();
  formData.append("file", file);

  // 2. Make a POST request to our FastAPI backend
  const response = await fetch(`${API_BASE_URL}/leases/`, {
    method: "POST",
    body: formData,
  });

  // 3. If the server returns an error (like a 500 or 400), throw an exception
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload file");
  }

  // 4. Parse and return the JSON response
  return response.json();
}

/**
 * Fetches the current status and details of a specific lease.
 * Used to check if processing is done!
 */
export async function getLease(leaseId: string): Promise<Lease> {
  const response = await fetch(`${API_BASE_URL}/leases/${leaseId}`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch lease data");
  }

  return response.json();
}

/**
 * Deletes a lease from the backend.
 */
export async function deleteLease(leaseId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/leases/${leaseId}`, {
    method: "DELETE",
  });
  
  if (!response.ok) {
    throw new Error("Failed to delete lease");
  }
}
```

> [!NOTE]
> We use the prefix `NEXT_PUBLIC_` for our environment variables so Next.js knows it is safe to include this variable in the frontend browser code. If a variable doesn't have this prefix, Next.js keeps it secret on the server!

---

## 10.5: WebSocket Hook

Now for the magic. We need to connect to our backend's WebSocket to receive the streaming AI responses (typing letter by letter).

React Hooks can be tricky with WebSockets because React components render multiple times, and we only want to connect *once*. We'll build a **Custom Hook** to manage this.

Create a folder `src/hooks` and a file `src/hooks/useWebSocket.ts`:

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useState, useEffect, useRef, useCallback } from "react";
import { WebSocketMessage } from "@/lib/types";

// Get the WebSocket URL. Note we change http:// to ws://
const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  .replace(/^http/, "ws");

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket(leaseId: string | null) {
  // --- STATE ---
  // useState holds data that, when changed, causes the screen to re-draw.
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  
  // --- REFS ---
  // useRef holds data that DOES NOT cause a re-draw when changed. 
  // It's like a secret pocket the component can keep notes in.
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // We let the caller provide a function to handle incoming messages
  const messageHandlerRef = useRef<(msg: WebSocketMessage) => void>();

  /**
   * We use this so the component can update its handler function
   * without triggering the WebSocket to disconnect and reconnect.
   */
  const onMessage = useCallback((handler: (msg: WebSocketMessage) => void) => {
    messageHandlerRef.current = handler;
  }, []);

  /**
   * Sends a text query to the backend over the active WebSocket.
   */
  const sendMessage = useCallback((query: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // The backend expects a JSON object: { "type": "query", "content": "my question" }
      wsRef.current.send(JSON.stringify({ type: "query", content: query }));
    } else {
      console.error("WebSocket is not connected");
    }
  }, []);

  /**
   * The main connection logic. Wrapped in useCallback so we can call it recursively for reconnects.
   */
  const connect = useCallback(() => {
    if (!leaseId) return;

    setConnectionState("connecting");
    
    // Create the connection to our FastAPI endpoint
    const ws = new WebSocket(`${WS_BASE_URL}/ws/chat/${leaseId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected!");
      setConnectionState("connected");
      reconnectAttemptsRef.current = 0; // Reset attempts on success
    };

    ws.onmessage = (event) => {
      try {
        // Parse the incoming JSON message from the backend
        const data: WebSocketMessage = JSON.parse(event.data);
        
        // Pass it to the handler if one was provided
        if (messageHandlerRef.current) {
          messageHandlerRef.current(data);
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message", e);
      }
    };

    ws.onclose = () => {
      setConnectionState("disconnected");
      
      // Exponential Backoff Reconnection strategy
      // 1s, 2s, 4s, 8s, up to max 30s
      const attempts = reconnectAttemptsRef.current;
      const backoffMs = Math.min(1000 * Math.pow(2, attempts), 30000);
      
      console.log(`WebSocket closed. Reconnecting in ${backoffMs}ms...`);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current += 1;
        connect();
      }, backoffMs);
    };

    ws.onerror = () => {
      // We don't set error state here because onclose will fire immediately after
      console.error("WebSocket error occurred");
    };
  }, [leaseId]);

  /**
   * useEffect runs automatically when the component mounts or when its dependencies (leaseId) change.
   */
  useEffect(() => {
    connect();

    // The return function is the "Cleanup Function".
    // React runs this when the component unmounts or before running the effect again.
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        // Remove the onclose handler so it doesn't try to reconnect when we intentionally close it
        wsRef.current.onclose = null; 
        wsRef.current.close();
      }
    };
  }, [connect]); // Only re-run if 'connect' changes (which only happens if leaseId changes)

  return {
    connectionState,
    sendMessage,
    onMessage
  };
}
```

### What just happened?
We created a robust WebSocket hook! 
- **`useRef` vs `useState`**: This is a core React concept. If you put the WebSocket inside `useState`, changing it would cause the component to redraw. We don't want the screen to redraw just because we saved a reference to the connection. So we put it in `useRef.current`.
- **Exponential Backoff**: If the connection drops, we don't spam the server. We wait 1 second, then 2, then 4, then 8. This is a professional-grade pattern for networking.
- **The Cleanup Function**: When you leave the chat page, React calls the `return () => { ... }` function in `useEffect`. This cleanly closes the WebSocket so we don't leak memory.

---

## 10.6: Chat Hook

Now let's build the hook that manages the list of messages in our chat window. It will use the WebSocket hook we just built.

Create `src/hooks/useChat.ts`:

```typescript
// frontend/src/hooks/useChat.ts
import { useState, useCallback, useEffect } from "react";
import { ChatMessage, Citation } from "@/lib/types";
import { useWebSocket } from "./useWebSocket";

export function useChat(leaseId: string | null) {
  // Store the list of messages in the chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // Are we currently receiving tokens from the AI?
  const [isStreaming, setIsStreaming] = useState(false);
  
  // Bring in our WebSocket hook
  const { connectionState, sendMessage, onMessage } = useWebSocket(leaseId);

  // Generate a random ID for new messages (UUID v4 format is best, but this is simple)
  const generateId = () => Math.random().toString(36).substring(2, 9);

  // Set up the listener for incoming WebSocket messages
  useEffect(() => {
    onMessage((msg) => {
      if (msg.type === "token") {
        setIsStreaming(true);
        // We use the "functional update" form of setMessages.
        // It gives us the *current* state (prev) so we can modify it safely.
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          
          // If the last message isn't from the assistant, create a new one
          if (!lastMsg || lastMsg.role !== "assistant") {
            const newAssistantMsg: ChatMessage = {
              id: generateId(),
              role: "assistant",
              content: msg.content,
              createdAt: new Date().toISOString(),
            };
            return [...prev, newAssistantMsg];
          }

          // Otherwise, append the new token to the existing assistant message
          const updatedMsg = {
            ...lastMsg,
            content: lastMsg.content + msg.content,
          };
          
          // Replace the last message in the array
          return [...prev.slice(0, -1), updatedMsg];
        });
      } 
      else if (msg.type === "citations") {
        // Attach citations to the current assistant message
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (!lastMsg || lastMsg.role !== "assistant") return prev;

          const updatedMsg = {
            ...lastMsg,
            citations: msg.data,
          };
          return [...prev.slice(0, -1), updatedMsg];
        });
      } 
      else if (msg.type === "done") {
        setIsStreaming(false);
      } 
      else if (msg.type === "error") {
        setIsStreaming(false);
        // Add a system error message to the chat
        const errorMsg: ChatMessage = {
          id: generateId(),
          role: "assistant",
          content: `*Error:* ${msg.message}`,
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    });
  }, [onMessage]);

  /**
   * Called when the user clicks "Send"
   */
  const sendQuery = useCallback((query: string) => {
    // 1. Don't send empty messages
    if (!query.trim()) return;

    // 2. Add the user's message to the chat immediately
    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content: query,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // 3. Send it to the backend via WebSocket
    sendMessage(query);
  }, [sendMessage]);

  return {
    messages,
    isStreaming,
    connectionState,
    sendQuery,
  };
}
```

### What just happened?
This hook acts as the "Brain" for our Chat window. 
When a `token` arrives, it checks: "Is the last message from the assistant?" 
- If no, it creates a new assistant message with that first word.
- If yes, it glues the new word onto the end of the existing message. 
Because `setMessages` updates React state, the screen redraws every time a token arrives, creating the typing effect!

---

## 10.7: Upload Hook

We need a hook to manage the state of our file upload and polling for readiness. Since vectorizing a PDF takes time, our backend returns `status: "processing"`. We need to keep checking back until it says `ready`.

Create `src/hooks/useLeaseUpload.ts`:

```typescript
// frontend/src/hooks/useLeaseUpload.ts
import { useState, useCallback } from "react";
import { uploadLease, getLease } from "@/lib/api";

type UploadStatus = "idle" | "uploading" | "processing" | "completed" | "error";

export function useLeaseUpload() {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0); // 0 to 100
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [readyLeaseId, setReadyLeaseId] = useState<string | null>(null);

  /**
   * Helper function that polls the backend every 2 seconds
   * until the lease is 'ready' or 'error'.
   */
  const pollProcessingStatus = async (leaseId: string) => {
    setStatus("processing");
    // Faux progress just for UI flair (goes from 50 to 95 slowly)
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
          // Still processing, bump faux progress a bit
          if (fauxProgress < 95) {
            fauxProgress += 5;
            setProgress(fauxProgress);
          }
        }
      } catch (e) {
        clearInterval(pollInterval);
        setStatus("error");
        setErrorMsg("Lost connection while checking status.");
      }
    }, 2000); // Check every 2 seconds
  };

  /**
   * Main function called when user drops a file
   */
  const uploadFile = useCallback(async (file: File) => {
    setStatus("uploading");
    setProgress(20); // Initial jump
    setErrorMsg(null);

    try {
      const response = await uploadLease(file);
      setProgress(50); // Upload complete, backend has it
      
      // Now start polling until it's indexed
      pollProcessingStatus(response.lease_id);
      
    } catch (e: any) {
      setStatus("error");
      setErrorMsg(e.message || "An error occurred during upload.");
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
```

---

## 10.8: UI Components

Now for the fun part: Building the visual blocks of our app! We will build these inside `src/components`.

### 1. The Button Component
Create `src/components/ui/Button.tsx`. We'll use `clsx` and `tailwind-merge` to combine Tailwind classes cleanly.

```tsx
// frontend/src/components/ui/Button.tsx
import React from "react";
import { Loader2 } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// A utility function to safely merge tailwind classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Extending standard HTML Button props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  isLoading?: boolean;
}

export function Button({ 
  children, 
  variant = "primary", 
  isLoading = false, 
  className,
  disabled,
  ...props 
}: ButtonProps) {
  
  // Base styles applied to all buttons
  const baseStyles = "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed";
  
  // Styles specific to the variant chosen
  const variants = {
    primary: "bg-primary text-white hover:bg-primary-hover shadow-lg shadow-primary/20 hover:shadow-primary/40 focus:ring-primary",
    secondary: "bg-surface border border-surface-border text-foreground hover:bg-white/5 focus:ring-white/20",
    ghost: "bg-transparent text-gray-400 hover:text-white hover:bg-white/10 focus:ring-white/20"
  };

  return (
    <button
      className={cn(baseStyles, variants[variant], "px-4 py-2", className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {/* If loading, show a spinning icon */}
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}
```

### 2. FileUpload Component
Create `src/components/FileUpload.tsx`. This handles dragging and dropping files.

```tsx
// frontend/src/components/FileUpload.tsx
import React, { useCallback, useState } from "react";
import { FileUp, File as FileIcon, X } from "lucide-react";
import { cn, Button } from "./ui/Button";

interface FileUploadProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
}

export function FileUpload({ onUpload, isLoading }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  // When user drags file over the zone
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault(); // Required to allow dropping
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  // When user drops the file
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setError(null);

    const file = e.dataTransfer.files[0];
    validateAndSelectFile(file);
  }, []);

  // When user clicks and selects a file via file browser
  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  }, []);

  const validateAndSelectFile = (file: File) => {
    // Check size (e.g., 20MB max)
    if (file.size > 20 * 1024 * 1024) {
      setError("File is too large. Max size is 20MB.");
      return;
    }
    // Check type (Very basic check)
    if (!file.type.includes("pdf") && !file.type.includes("image")) {
      setError("Only PDFs and Images are supported.");
      return;
    }
    setSelectedFile(file);
  };

  const handleUploadClick = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      {!selectedFile ? (
        // The Dropzone Area
        <label 
          className={cn(
            "glass-panel flex flex-col items-center justify-center w-full h-64 rounded-2xl cursor-pointer transition-all duration-300 border-2 border-dashed",
            isDragging ? "border-primary bg-primary/5" : "border-surface-border hover:border-gray-400"
          )}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
            <div className="p-4 bg-surface rounded-full mb-4 shadow-lg">
              <FileUp className="w-8 h-8 text-primary" />
            </div>
            <p className="mb-2 text-lg font-semibold">Click to upload or drag and drop</p>
            <p className="text-sm text-gray-400">PDF, JPG, PNG or TIFF (MAX. 20MB)</p>
          </div>
          <input 
            type="file" 
            className="hidden" 
            accept=".pdf,image/*" 
            onChange={onFileChange}
          />
        </label>
      ) : (
        // File Selected View
        <div className="glass-panel p-6 rounded-2xl animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary/20 rounded-lg text-primary">
                <FileIcon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium truncate max-w-[200px] sm:max-w-[300px]">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-gray-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button 
              onClick={() => setSelectedFile(null)}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              disabled={isLoading}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <Button 
            className="w-full" 
            onClick={handleUploadClick}
            isLoading={isLoading}
          >
            {isLoading ? "Processing..." : "Analyze Document"}
          </Button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm text-center animate-slide-up">
          {error}
        </div>
      )}
    </div>
  );
}
```

### 3. ProcessingStatus Component
Create `src/components/ProcessingStatus.tsx`. Shows progress while the backend vectorizes the PDF.

```tsx
// frontend/src/components/ProcessingStatus.tsx
import React from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { cn } from "./ui/Button";

interface ProcessingStatusProps {
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  progress: number;
}

export function ProcessingStatus({ status, progress }: ProcessingStatusProps) {
  // Define our steps based on current status
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

      {/* Progress Bar */}
      <div className="w-full bg-surface border border-surface-border rounded-full h-2 mb-8 overflow-hidden">
        <div 
          className="bg-primary h-2 rounded-full transition-all duration-500 ease-out" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>

      {/* Step List */}
      <div className="space-y-4">
        {steps.map((step, index) => {
          // Determine state of this specific step
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
```

### 4. MessageBubble Component
Create `src/components/MessageBubble.tsx`. This renders individual chat messages and supports Markdown!

```tsx
// frontend/src/components/MessageBubble.tsx
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm"; // Adds support for tables, task lists, etc.
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
        
        {/* Avatar Icon */}
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1",
          isUser ? "ml-3 bg-primary" : "mr-3 bg-surface border border-surface-border",
        )}>
          {isUser ? <User className="w-5 h-5 text-white" /> : <Sparkles className="w-5 h-5 text-primary" />}
        </div>

        {/* Message Content Bubble */}
        <div className={cn(
          "px-5 py-4 rounded-2xl",
          isUser ? "bg-primary text-white rounded-tr-sm" : "glass-panel rounded-tl-sm"
        )}>
          
          {/* Render Markdown! prose classes style the HTML output of ReactMarkdown */}
          <div className={cn(
            "prose prose-sm max-w-none leading-relaxed",
            isUser ? "prose-invert text-white" : "prose-invert"
          )}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            
            {/* Animated Typing Indicator */}
            {isStreaming && (
              <span className="inline-flex space-x-1 ml-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse-dot" style={{ animationDelay: "0ms" }}/>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse-dot" style={{ animationDelay: "200ms" }}/>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse-dot" style={{ animationDelay: "400ms" }}/>
              </span>
            )}
          </div>

          {/* Citations block (if the assistant provided them) */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-white/10">
              <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wider">Sources</p>
              <div className="flex flex-wrap gap-2">
                {message.citations.map((cite, idx) => (
                  <div key={idx} className="group relative">
                    {/* The Badge */}
                    <span className="inline-flex items-center px-2 py-1 rounded bg-white/5 border border-white/10 text-xs text-gray-300 cursor-help hover:bg-white/10 transition-colors">
                      Page {cite.pageNumber}
                    </span>
                    
                    {/* Tooltip on hover */}
                    <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 text-xs">
                      {cite.sectionTitle && <p className="font-bold text-white mb-1">{cite.sectionTitle}</p>}
                      <p className="text-gray-300 italic line-clamp-4">"{cite.snippet}"</p>
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
```

### 5. ChatInput Component
Create `src/components/ChatInput.tsx`. An auto-expanding textarea for typing queries.

```tsx
// frontend/src/components/ChatInput.tsx
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

  // Auto-resize the textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "inherit";
      const computed = window.getComputedStyle(textareaRef.current);
      const height = textareaRef.current.scrollHeight;
      // Cap height at roughly 4 lines (96px)
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
    // Send on Enter, unless Shift is held down (which makes a new line)
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
```

---

## 10.9: Pages (Putting it all together)

Next.js uses a folder-based routing system. The `src/app/page.tsx` file is the homepage (`/`), and we'll create `src/app/chat/[leaseId]/page.tsx` for the chat page.

### 1. The Home Page (Upload)
Overwrite `src/app/page.tsx`:

```tsx
// frontend/src/app/page.tsx
"use client"; // Tells Next.js this component uses browser features (like React Hooks)

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, FileText, Search } from "lucide-react";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { useLeaseUpload } from "@/hooks/useLeaseUpload";

export default function Home() {
  const router = useRouter(); // For navigating to a new URL
  const { uploadFile, status, progress, errorMsg, readyLeaseId } = useLeaseUpload();

  // Watch for when the lease is ready, then redirect to the chat page!
  useEffect(() => {
    if (status === "completed" && readyLeaseId) {
      // Small delay just so the user sees the 100% complete state
      setTimeout(() => {
        router.push(`/chat/${readyLeaseId}`);
      }, 1000);
    }
  }, [status, readyLeaseId, router]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      
      {/* Cool background glow effects */}
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
        {/* If idle or error, show upload box. If processing, show progress. */}
        {status === "idle" || status === "error" ? (
          <FileUpload onUpload={uploadFile} isLoading={status === "uploading"} />
        ) : (
          <ProcessingStatus status={status} progress={progress} />
        )}

        {status === "error" && errorMsg && (
          <p className="text-red-400 text-center mt-4">{errorMsg}</p>
        )}
      </div>

      {/* Feature blurbs */}
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
```

### 2. The Chat Page
Create the folders `src/app/chat/[leaseId]` and then create `src/app/chat/[leaseId]/page.tsx`.

> [!NOTE]
> The brackets `[leaseId]` in the folder name is Next.js's way of creating a **Dynamic Route**. If you go to `/chat/123-abc`, Next.js will pass `123-abc` to the component as a parameter named `leaseId`.

```tsx
// frontend/src/app/chat/[leaseId]/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, AlertCircle } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { getLease } from "@/lib/api";
import { Lease } from "@/lib/types";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { Button } from "@/components/ui/Button";

export default function ChatPage() {
  const params = useParams(); // Gets variables from the URL
  const router = useRouter();
  const leaseId = params.leaseId as string;
  
  const [lease, setLease] = useState<Lease | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize our Chat hook!
  const { messages, isStreaming, sendQuery, connectionState } = useChat(leaseId);
  
  // A reference to the bottom of the message list so we can auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Fetch lease details on load to get the filename
  useEffect(() => {
    async function loadLease() {
      try {
        const data = await getLease(leaseId);
        if (data.status !== "completed") {
          setError("This document is not ready yet.");
        } else {
          setLease(data);
        }
      } catch (e) {
        setError("Document not found.");
      }
    }
    loadLease();
  }, [leaseId]);

  // 2. Auto-scroll to bottom when messages change
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

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      
      {/* Header */}
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

      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            // Empty State
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
                    "{q}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Message List
            <div className="pb-4">
              {messages.map((msg, index) => (
                <MessageBubble 
                  key={msg.id} 
                  message={msg} 
                  // Pass true to isStreaming ONLY for the very last message, IF we are currently streaming
                  isStreaming={isStreaming && index === messages.length - 1 && msg.role === "assistant"}
                />
              ))}
              {/* Invisible div to scroll to */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
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
```

---

## 10.10: Running the Frontend

You're done coding! Let's fire it up.

1. Ensure your backend is running in a separate terminal:
   ```powershell
   cd leasegpt/backend
   poetry run uvicorn main:app --reload
   ```

2. Open a new terminal for the frontend.
3. Make sure you are in `leasegpt/frontend`.
4. Install all the dependencies you added:
   ```powershell
   npm install
   ```
5. (Optional) Create a `.env.local` file in the `frontend` folder if your backend isn't on `localhost:8000`. By default, our code falls back to `localhost:8000`, so you can skip this if you're running locally.
6. Start the Next.js development server:
   ```powershell
   npm run dev
   ```

7. Open your browser and go to `http://localhost:3000`.

You should see your stunning new dark-mode interface! 
Try dragging a PDF lease into the drop zone. Watch the progress bar go as the backend processes it. When it finishes, you'll be whisked away to the chat page where you can start asking questions. As the AI replies, you'll see the words stream in smoothly, just like ChatGPT!

**Congratulations!** You have built a complete full-stack AI application using FastAPI, LangGraph, vector databases, and Next.js!
