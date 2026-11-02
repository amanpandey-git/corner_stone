// Online demo: server-only helpers for the /api/demo/* routes (Groq calls, exported slides, answer JSON).
// The Groq request mirrors GroqProvider in llm.py: same model, prompts, max tokens, temperature and extra settings.
import "server-only";
import chunksData from "@/public/demo/chunks.json";
import metaData from "@/public/demo/meta.json";
import { label, type ChunkRec, type Citation, type DemoMeta, type Finalised, type Source } from "./core";

export const meta = metaData as unknown as DemoMeta;
export const chunks = chunksData as unknown as ChunkRec[];
export const byId = new Map(chunks.map((c) => [c.id, c]));

const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";
const TIMEOUT_MS = 60_000;      // whole call including the stream (llm.timeout_s in Python is per read)
const RETRYABLE = [429, 500, 502, 503, 504];

export class DemoError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const jsonError = (e: unknown) => {
  const status = e instanceof DemoError ? e.status : 500;
  return Response.json({ detail: e instanceof Error ? e.message : String(e) }, { status });
};

export function groqKey(): string {
  const key = process.env.GROQ_API_KEY;
  if (!key) throw new DemoError(503, "GROQ_API_KEY is not set on the server (Vercel: Settings -> Environment Variables)");
  return key;
}

type Which = "groq" | "groq_judge";

function body(which: Which, system: string, user: string, maxTokens: number, temperature: number, stream: boolean, jsonMode: boolean) {
  const b: Record<string, unknown> = {
    model: meta.llm[which].model,
    messages: [
      { role: "system", content: system },
      { role: "user", content: user },
    ],
    max_completion_tokens: maxTokens,
    temperature,
    stream,
    ...meta.llm[which].extra,
  };
  if (jsonMode) b.response_format = { type: "json_object" };
  return b;
}

/** Status + Groq's error type only, like _error() in llm.py: an error body may echo the request. */
async function groqError(res: Response, model: unknown): Promise<DemoError> {
  const kind = await res.json().then((b) => b?.error?.type ?? "", () => "");
  const msg = `Groq ${model}: HTTP ${res.status} ${kind}`.trim();
  if (res.status === 401 || res.status === 403) return new DemoError(503, `${msg} (key refused; check GROQ_API_KEY)`);
  if (res.status === 404) return new DemoError(503, `${msg} (model not found)`);
  if (res.status === 429) return new DemoError(503, `${msg}: Groq's free-tier rate limit was reached; wait a minute and try again`);
  return new DemoError(503, msg);
}

/** _retry_wait() in llm.py: seconds before retry number `attempt`, or null to give up now. */
function retryWait(attempt: number, res: Response | null): number | null {
  const { max_retries, backoff_s, max_backoff_s } = meta.llm;
  if (attempt > max_retries) return null;
  const wait = Math.min(backoff_s * 2 ** (attempt - 1), max_backoff_s);
  const header = res?.status === 429 ? res.headers.get("retry-after") : null;
  const ra = header === null ? NaN : Number(header);
  if (Number.isNaN(ra)) return wait;
  return ra > max_backoff_s ? null : Math.max(wait, ra);
}

/** POST to Groq with the capped retries of _send() in llm.py (429, 5xx, timeouts, connection errors). */
async function send(payload: Record<string, unknown>): Promise<Response> {
  const key = groqKey();
  for (let attempt = 1; ; attempt++) {
    let res: Response | null = null;
    try {
      res = await fetch(GROQ_URL, {
        method: "POST",
        headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
    } catch {
      /* timeout or connection error: res stays null, retried below */
    }
    if (res?.ok) return res;
    if (res && !RETRYABLE.includes(res.status)) throw await groqError(res, payload.model);
    const wait = retryWait(attempt, res);
    if (wait === null) {
      if (res) throw await groqError(res, payload.model);
      throw new DemoError(503, "Groq did not respond in time; try again");
    }
    await res?.body?.cancel();
    await sleep(wait * 1000);
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function complete(which: Which, system: string, user: string, maxTokens: number, temperature: number, jsonMode = false) {
  const res = await send(body(which, system, user, maxTokens, temperature, false, jsonMode));
  const data = await res.json();
  const text = String(data?.choices?.[0]?.message?.content ?? "").trim();
  if (!text) throw new DemoError(503, `Groq ${meta.llm[which].model}: empty reply`);
  return text;
}

/** Text pieces of a streamed reply (choices[0].delta.content; reasoning tokens are skipped). */
export async function* stream(system: string, user: string, maxTokens: number, temperature: number): AsyncGenerator<string> {
  const res = await send(body("groq", system, user, maxTokens, temperature, true, false));
  if (!res.body) throw new DemoError(503, "Groq returned an empty stream");
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let empty = true;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;
      let nl: number;
      while ((nl = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, nl).trim();
        buffer = buffer.slice(nl + 1);
        if (!line.startsWith("data:")) continue;
        const data = line.slice(5).trim();
        if (data === "[DONE]") {
          buffer = "";
          await reader.cancel();
          break;
        }
        let piece: unknown;
        try {
          piece = JSON.parse(data)?.choices?.[0]?.delta?.content;
        } catch {
          continue;       // keep-alive or partial line
        }
        if (piece) {
          empty = false;
          yield piece as string;
        }
      }
    }
    // an empty reply is a provider failure, never "Not in your notes." (llm.py raises here too)
    if (empty) throw new DemoError(503, `Groq ${meta.llm.groq.model}: empty reply`);
  } finally {
    await reader.cancel().catch(() => {});   // also runs when the browser stops reading the answer
  }
}

// ------------------------------------------------------------------ JSON in the same shape as api.py
export const imageUrl = (c: ChunkRec | undefined | null) => c?.image ?? null;

export function answerJson(
  question: string,
  mode: string,
  sources: Source[],
  f: Finalised,
  extra: { unsupported: number[] | null; check_error: string | null; ttft_ms: number | null; total_ms: number },
) {
  const cited = new Set(f.citations.flatMap((c: Citation) => c.refs));
  return {
    question,
    mode,
    text: f.text,
    abstained: f.abstained,
    abstain_reason: f.abstain_reason,
    citations: f.citations,
    sources: sources.map((s) => ({
      n: s.n,
      file_name: s.chunk.file_name,
      doc_id: s.chunk.doc_id,
      page_start: s.chunk.page_start,
      page_end: s.chunk.page_end,
      section: s.chunk.section,
      label: label(s.chunk),
      text: s.chunk.text,
      cited: cited.has(s.n),
      image_url: imageUrl(s.chunk),
    })),
    uncited_sentences: f.uncited_sentences,
    invalid_refs: f.invalid_refs,
    unsupported: extra.unsupported,
    check_error: extra.check_error,
    provider: "groq",
    model: meta.llm.groq.model,
    cached: false,
    ttft_ms: extra.ttft_ms,
    total_ms: extra.total_ms,
  };
}

export function quizSourceJson(s: Source) {
  return {
    n: s.n,
    file_name: s.chunk.file_name,
    page: s.chunk.page_start,
    doc_id: s.chunk.doc_id,
    chunk_id: s.chunk.id,
    section: s.chunk.section,
    label: label(s.chunk),
    image_url: imageUrl(s.chunk),
  };
}
