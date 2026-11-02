// POST /api/demo/ask: stream_answer() in answer.py + /ask/stream in api.py. Retrieval already ran in the browser,
// which sends chunk ids; the prompt is built only from this server's own copy of those chunks.
import { buildJudgePrompt, buildPrompt, finalise, MODES, NOT_IN_NOTES, NOT_IN_NOTES_TOKEN, parseJudgeReply, type Finalised, type Source } from "@/lib/demo/core";
import { answerJson, byId, complete, DemoError, groqKey, jsonError, meta, stream } from "@/lib/demo/server";

export const maxDuration = 120;

const HOLD = NOT_IN_NOTES_TOKEN.length;   // streamed text is held back until it cannot be the abstention token

/** check_citations() in citations.py: one retry on malformed JSON, then "could not be checked", never "all fine". */
async function judge(f: Finalised, sources: Source[]) {
  const texts = new Map(sources.map((s) => [s.n, s.chunk.text]));
  const user = buildJudgePrompt(f.citations, texts);
  try {
    for (let attempt = 0; attempt < 2; attempt++) {
      const system = meta.prompts.judge_system + (attempt ? " Reply with the JSON object only." : "");
      const reply = await complete("groq_judge", system, user, meta.answer.judge_max_tokens, 0, true);
      const unsupported = parseJudgeReply(reply, f.citations.length);
      if (unsupported) return { unsupported, check_error: null };
    }
    return { unsupported: null, check_error: "judge reply was not valid JSON (twice)" };
  } catch (e) {
    return { unsupported: null, check_error: e instanceof Error ? e.message : String(e) };
  }
}

export async function POST(req: Request) {
  const t0 = performance.now();
  try {
    const body = await req.json().catch(() => null);
    const question = typeof body?.question === "string" ? body.question : "";
    const mode = body?.mode ?? "concise";
    const ids: unknown = body?.ids;
    if (!question.trim()) throw new DemoError(422, "question is empty");
    if (question.length > meta.search.max_query_chars) throw new DemoError(422, `question is longer than ${meta.search.max_query_chars} characters`);
    if (!MODES.includes(mode)) throw new DemoError(422, `unknown mode ${JSON.stringify(mode)}; choose one of ${MODES.join(", ")}`);
    if (!Array.isArray(ids) || ids.length > meta.answer.k) throw new DemoError(422, `ids must be a list of at most ${meta.answer.k} chunk ids`);
    const sources: Source[] = ids.map((id, i) => {
      const chunk = byId.get(id);
      if (!chunk) throw new DemoError(422, `no chunk with id ${JSON.stringify(id)}`);
      return { n: i + 1, chunk };
    });
    groqKey();            // 503 before the stream starts, like provider() in api.py

    let closed = false;
    const encoder = new TextEncoder();
    const events = new ReadableStream<Uint8Array>({
      async start(controller) {
        const send = (kind: string, data: unknown) => {
          if (!closed) controller.enqueue(encoder.encode(`event: ${kind}\ndata: ${JSON.stringify(data)}\n\n`));
        };
        const elapsed = () => performance.now() - t0;
        try {
          if (!sources.length || !(body.top_score >= meta.answer.min_vector_score)) {
            const f: Finalised = { text: NOT_IN_NOTES, abstained: true, abstain_reason: "retrieval", citations: [], uncited_sentences: [], invalid_refs: [] };
            send("final", answerJson(question, mode, sources, f, { unsupported: null, check_error: null, ttft_ms: null, total_ms: elapsed() }));
            return;
          }
          const [system, user] = buildPrompt(question, sources, mode, meta);
          let raw = "";
          let ttft: number | null = null;
          let released = false;   // becomes true once the reply cannot be NOT_IN_NOTES
          for await (const delta of stream(system, user, meta.answer.modes[mode].max_tokens, meta.llm.temperature)) {
            if (closed) return;
            ttft ??= elapsed();
            raw += delta;
            if (released) {
              send("delta", delta);
              continue;
            }
            const soFar = raw.trimStart();
            if (soFar.length >= HOLD && !soFar.toUpperCase().startsWith(NOT_IN_NOTES_TOKEN)) {
              released = true;
              send("delta", soFar);
            }
          }
          const f = finalise(raw, sources.length);
          if (!released && !f.abstained) send("delta", f.text);   // a reply shorter than the hold-back window
          const total = elapsed();
          const checked = body.check === true && !f.abstained ? await judge(f, sources) : { unsupported: null, check_error: null };
          send("final", answerJson(question, mode, sources, f, { ...checked, ttft_ms: ttft, total_ms: total }));
        } catch (e) {
          send("error", { detail: e instanceof Error ? e.message : String(e) });
        } finally {
          if (!closed) controller.close();
        }
      },
      cancel() {
        closed = true;    // the student asked something else or left the page: stop reading from Groq
      },
    });
    return new Response(events, {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no" },
    });
  } catch (e) {
    return jsonError(e);
  }
}
