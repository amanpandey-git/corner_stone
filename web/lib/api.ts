// Thin typed client for the Cornerstone HTTP API (ARCHITECTURE.md 13 + 14).
// No retrieval, answering, quiz or SM-2 logic lives in the web app: every function here is one HTTP call.

export const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export const MODES = ["concise", "detailed", "2-mark", "5-mark", "10-mark"] as const;
export type Mode = (typeof MODES)[number];

// ------------------------------------------------------------------ types (mirror the API's JSON)
export type Health = {
  status: string;
  documents: number;
  chunks: number;
  schema_version: number;
  llm_provider: string;
  llm_key_present: boolean;
  rerank: boolean;
  hybrid: boolean;
};

export type DocumentRow = {
  doc_id: number;
  file_name: string;
  unit: string | null;
  pages_total: number;
  pages_with_text: number;
  pages_flagged: number;
  pages_duplicate: number;
  chunks: number;
  status: string;
  ingested_at: string;
};

/** IngestReport from pipeline.ingest_file (a crash outside it only sets `message`). */
export type IngestReport = {
  file_name?: string;
  status?: "indexed" | "replaced" | "skipped_duplicate" | "failed";
  doc_id?: number | null;
  pages_total?: number;
  pages_with_text?: number;
  pages_flagged?: number;
  flagged_pages?: [number | null, string][];
  chunks_created?: number;
  pages_duplicate?: number;
  duplicate_pages?: [number, number][];
  warnings?: string[];
  seconds?: number;
  message: string;
};

export type Job = {
  job_id: string;
  file_name: string;
  state: "queued" | "running" | "done" | "failed";
  report: IngestReport | null;
};

export type Source = {
  n: number;
  file_name: string;
  doc_id: number;
  page_start: number | null;
  page_end: number | null;
  section: string | null;
  label: string;
  text: string;
  cited: boolean;
  image_url: string | null;
};

export type Answer = {
  question: string;
  mode: Mode;
  text: string;
  abstained: boolean;
  abstain_reason: string | null;
  citations: { sentence: string; refs: number[] }[];
  sources: Source[];
  uncited_sentences: string[];
  invalid_refs: number[];
  unsupported: number[] | null;
  check_error: string | null;
  provider: string;
  model: string;
  cached: boolean;
  ttft_ms: number | null;
  total_ms: number | null;
};

export type AskBody = { question: string; mode: Mode; units?: string[]; check?: boolean };

export type QuizSource = {
  n: number;
  file_name: string;
  page: number | null;
  doc_id: number | null;
  chunk_id: number | null;
  section: string | null;
  label: string;
  image_url: string | null;
};

export type QuizQuestion = {
  question: string;
  options: string[];
  answer: number;
  explanation: string;
  source: QuizSource;
};

export type Quiz = {
  requested: number;
  generated: number;
  attempts: number;
  rejected: unknown[];
  questions: QuizQuestion[];
};

export type Card = {
  card_id: number;
  front: string;
  back: string;
  file_name: string;
  page: number | null;
  doc_id: number | null;
  chunk_id: number | null;
  unit: string | null;
  due: string;
  ef: number;
  interval: number;
  reps: number;
  lapses: number;
  origin: string;
  image_url?: string | null;
};

export type Due = { today: string; cards: Card[]; stats: { cards: number; due_today: number; reviews: number } };

// ------------------------------------------------------------------ errors + requests
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const DOWN = `API not reachable at ${API}. Start it with: PYTHONPATH=src uvicorn cornerstone.api:app --port 8000`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(API + path, init);
  } catch {
    throw new ApiError(0, DOWN);
  }
  if (!res.ok) throw new ApiError(res.status, await detail(res));
  return (res.status === 204 ? undefined : await res.json()) as T;
}

async function detail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join("; ");
  } catch {
    /* not JSON */
  }
  return `HTTP ${res.status}`;
}

export const getJSON = <T>(path: string) => request<T>(path);

export const postJSON = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const del = (path: string) => request<void>(path, { method: "DELETE" });

export function uploadFiles(files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return request<{ jobs: { job_id: string; file_name: string }[] }>("/documents", { method: "POST", body: form });
}

/** Absolute URL for an image path returned by the API (`/pages/{doc}/{page}/image`), or null. */
export const imageSrc = (url: string | null | undefined) => (url ? API + url : null);

/** Error text for display; anything that is not an ApiError is shown by its message. */
export const errorText = (e: unknown) => (e instanceof Error ? e.message : String(e));

// ------------------------------------------------------------------ streaming answer (Server-Sent Events over POST)
/**
 * POST /ask/stream and read the event stream: `delta` events carry text pieces (passed to onDelta),
 * one `final` event carries the Answer JSON (returned), an `error` event becomes an ApiError.
 * EventSource cannot send a POST body, so the stream is read from fetch() with a ReadableStream.
 */
export async function streamAsk(body: AskBody, onDelta: (text: string) => void, signal?: AbortSignal): Promise<Answer> {
  let res: Response;
  try {
    res = await fetch(API + "/ask/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (signal?.aborted) throw e;
    throw new ApiError(0, DOWN);
  }
  if (!res.ok || !res.body) throw new ApiError(res.status, await detail(res));

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let final: Answer | null = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, "\n");
    let end: number;
    while ((end = buffer.indexOf("\n\n")) >= 0) {        // one SSE event ends with a blank line
      const raw = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      // [^\n] rather than "." so a U+2028 inside the JSON (ensure_ascii=False) cannot cut the data line
      const event = raw.match(/^event: ([^\n]*)$/m)?.[1];
      const data = raw.match(/^data: ([^\n]*)$/m)?.[1];
      if (!event || data === undefined) continue;
      const parsed = JSON.parse(data);
      if (event === "delta") onDelta(parsed as string);
      else if (event === "final") final = parsed as Answer;
      else if (event === "error") throw new ApiError(503, parsed.detail ?? "answer failed");
    }
  }
  if (!final) throw new ApiError(0, "the answer stream ended without a final answer");
  return final;
}
