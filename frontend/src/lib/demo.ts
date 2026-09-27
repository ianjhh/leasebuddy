import { Citation, Lease } from "./types";
import demoData from "./demo-data.json";

// Set at build time for the static demo (bun run build:demo). The demo has no
// backend: it opens a sample lease and replays answers the real agent gave in
// the evaluation run, exported by backend/evals/export_demo.py.
export const IS_DEMO = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

export interface DemoAnswer {
  question: string;
  category: string;
  answer: string;
  citations: Citation[];
  latencySeconds: number;
  retrievalPasses: number;
}

export const DEMO_LEASE = demoData.lease as Lease;
export const DEMO_SUGGESTED: string[] = demoData.suggested;
export const DEMO_ANSWERS: DemoAnswer[] = demoData.answers;

const normalize = (text: string) => text.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

export function findDemoAnswer(question: string): DemoAnswer | undefined {
  const target = normalize(question);
  return DEMO_ANSWERS.find((a) => normalize(a.question) === target);
}
