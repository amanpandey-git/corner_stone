// Plain-language errors for the page. The real detail goes to the console, never onto the screen.
// lib/api.ts keeps throwing exactly what it throws; this only decides how it reads.
import { ApiError, DEMO } from "./api";
import { DEMO_OFF } from "./demo/core";

export type Friendly = {
  kind: "rate" | "connection" | "model" | "input" | "other";
  title: string;
  text: string;
  /** Would asking again help? Decides whether a "Try again" button appears. */
  retry: boolean;
};

export function friendlyError(e: unknown): Friendly {
  const raw = e instanceof Error ? e.message : String(e);
  const status = e instanceof ApiError ? e.status : null;

  // Without the demo flag this is a developer's own machine, and the message says which command to run.
  if (!DEMO && raw.startsWith("API not reachable")) {
    return { kind: "connection", title: "The API is not running", text: raw, retry: true };
  }
  if (raw === DEMO_OFF) return { kind: "input", title: "Read-only in this demo", text: raw, retry: false };

  console.error("[synapse]", raw);

  if (/rate limit/i.test(raw) || status === 429) {
    return {
      kind: "rate",
      title: "The free AI quota is busy",
      text: "Wait a minute and try again. Nothing is wrong with your question.",
      retry: true,
    };
  }
  if (/search model/i.test(raw)) {
    return {
      kind: "model",
      title: "The search model did not download",
      text: "This browser could not download it. Try again, or use a different network.",
      retry: true,
    };
  }
  if (status === 0 || /could not reach|could not be reached|failed to fetch|networkerror/i.test(raw)) {
    return {
      kind: "connection",
      title: "Could not reach the demo",
      text: "Check your connection and try again.",
      retry: true,
    };
  }
  if (status === 422) {
    return {
      kind: "input",
      title: /longer than/.test(raw) ? "That is a very long question" : "That could not be processed",
      text: /longer than/.test(raw) ? "Please shorten it and try again." : "Please check what you entered and try again.",
      retry: false,
    };
  }
  if (status === 503) {
    return {
      kind: "other",
      title: "The answer service is unavailable",
      text: "Search still works, but no answer could be written just now. Try again shortly.",
      retry: true,
    };
  }
  return { kind: "other", title: "Something went wrong", text: "Please try again.", retry: true };
}
