import { DEMO_LEASE } from "@/lib/demo";
import { ChatView } from "./ChatView";

// A static export must know every page up front, so pre-render the demo's
// sample lease. Other lease IDs still render on demand in the normal build.
export function generateStaticParams() {
  return [{ leaseId: DEMO_LEASE.id }];
}

export default function ChatPage() {
  return <ChatView />;
}
