// Online demo (NEXT_PUBLIC_DEMO=1): the browser half, reached through lib/api.ts so the pages stay the same.
// Search runs here (no Python server); Groq calls go through /api/demo/*, flashcards live in localStorage.
// Contract: ARCHITECTURE.md 15.
import { ApiError, detail, readAnswerStream, type Answer, type AskBody, type Card, type Due, type DocumentRow, type QuizQuestion } from "../api";
import { collapse, DEMO_OFF, sm2, type ChunkRec, type DemoMeta } from "./core";

const TRANSFORMERS_URL = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.1/dist/transformers.min.js";
const MODEL = "Xenova/bge-small-en-v1.5";   // the ONNX export of the indexing model, BAAI/bge-small-en-v1.5
const CARDS_KEY = "synapse-demo-flashcards";

type Extractor = (text: string, opts: { pooling: "cls"; normalize: boolean }) => Promise<{ data: Float32Array }>;
type Transformers = { pipeline: (task: string, model: string, opts: { dtype: string }) => Promise<Extractor> };
type Dataset = { meta: DemoMeta; chunks: ChunkRec[]; vectors: Float32Array };

// ------------------------------------------------------------------ exported data + model, each loaded once
let dataset: Promise<Dataset> | null = null;
let extractor: Promise<Extractor> | null = null;

async function fetchOk(url: string): Promise<Response> {
  const res = await fetch(url).catch(() => null);
  if (!res) throw new ApiError(0, `Could not reach ${url}; check the connection and try again`);
  if (!res.ok) throw new ApiError(res.status, `${url}: HTTP ${res.status}`);
  return res;
}

function loadData(): Promise<Dataset> {
  dataset ??= (async () => {
    const [meta, chunks, raw] = await Promise.all([
      fetchOk("/demo/meta.json").then((r) => r.json() as Promise<DemoMeta>),
      fetchOk("/demo/chunks.json").then((r) => r.json() as Promise<ChunkRec[]>),
      fetchOk("/demo/vectors.f32").then((r) => r.arrayBuffer()),
    ]);
    const vectors = new Float32Array(raw);
    if (vectors.length !== chunks.length * meta.dim)
      throw new ApiError(0, `demo data is out of sync: ${vectors.length} numbers for ${chunks.length} chunks of dimension ${meta.dim}`);
    return { meta, chunks, vectors };
  })().catch((e) => {
    dataset = null;       // a failed download can be retried by the next question
    throw e;
  });
  return dataset;
}

function loadModel(): Promise<Extractor> {
  extractor ??= (async () => {
    // new Function hides the import from the bundler, so the library is only ever loaded from the CDN, in the browser
    const load = new Function("u", "return import(u)") as (u: string) => Promise<Transformers>;
    const { pipeline } = await load(TRANSFORMERS_URL);
    return pipeline("feature-extraction", MODEL, { dtype: "q8" });
  })().catch((e) => {
    extractor = null;
    throw new ApiError(0, `Could not load the search model in this browser: ${e instanceof Error ? e.message : e}`);
  });
  return extractor;
}

/** Embedder.embed_query() in embeddings.py: prefix + first max_query_chars, CLS pooling, unit length. */
async function embedQuery(query: string, meta: DemoMeta): Promise<Float32Array> {
  const model = await loadModel();
  const text = meta.embedding.query_prefix + query.trim().slice(0, meta.search.max_query_chars);
  return (await model(text, { pooling: "cls", normalize: true })).data;
}

/** Cosine similarity of every chunk (dot product of unit vectors), best first; exact, so there is no ANN recall loss. */
function rank(q: Float32Array, { chunks, vectors, meta }: Dataset, units?: string[]) {
  const hits: { chunk: ChunkRec; score: number }[] = [];
  chunks.forEach((chunk, i) => {
    if (units?.length && !units.includes(chunk.unit ?? "")) return;
    let score = 0;
    for (let d = 0; d < meta.dim; d++) score += q[d] * vectors[i * meta.dim + d];
    hits.push({ chunk, score });
  });
  return hits.sort((a, b) => b.score - a.score);
}

/** search() in search.py with its live settings: top candidates -> collapse near-copies -> first k. */
async function search(question: string, units?: string[]) {
  const data = await loadData();
  const { meta } = data;
  const top = rank(await embedQuery(question, meta), data, units).slice(0, meta.retrieval.candidates);
  const kept = meta.retrieval.collapse ? collapse(top, meta.dedup.result_jaccard) : top;
  return kept.slice(0, meta.answer.k);
}

/** Does the q8 browser model rank like the real model? Compares against meta.self_check; result in the console. */
async function selfCheck(): Promise<void> {
  const data = await loadData();
  const want = data.meta.self_check;
  const hits = rank(await embedQuery(want.query, data.meta), data).slice(0, want.top_ids.length);
  const got = hits.map((h) => h.chunk.id);
  const same = got.join() === want.top_ids.join();
  const report = `[demo self-check] top ${got.length} ${same ? "match" : "DIFFER"}: browser ${got.join(",")} (${hits[0]?.score.toFixed(4)}), Python ${want.top_ids.join(",")} (${want.top_scores[0]})`;
  if (same) console.info(report);
  else console.warn(report);
}

let warm = false;

/** Start the downloads before the first question, so it is not the one that waits for them. */
function warmUp(): void {
  if (warm) return;
  warm = true;
  // a failure here is reported again, on screen, by the question that needs the model
  selfCheck().catch((e) => {
    warm = false;
    console.warn(`[demo self-check] not run: ${e instanceof Error ? e.message : e}`);
  });
}

// ------------------------------------------------------------------ /api/demo/* calls
async function server<T>(path: string, body?: unknown): Promise<T> {
  const init = body === undefined ? undefined
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, init).catch(() => null);
  if (!res) throw new ApiError(0, "The online demo's server could not be reached; check the connection and try again");
  if (!res.ok) throw new ApiError(res.status, await detail(res));
  return (await res.json()) as T;
}

/** POST /ask/stream: retrieval here, then the server answers from the chosen chunk ids. */
export async function demoStreamAsk(body: AskBody, onDelta: (text: string) => void, signal?: AbortSignal): Promise<Answer> {
  if (!body.question.trim()) throw new ApiError(422, "question is empty");
  const hits = await search(body.question, body.units);
  const res = await fetch("/api/demo/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: body.question,
      mode: body.mode,
      ids: hits.map((h) => h.chunk.id),
      top_score: hits.length ? Math.max(...hits.map((h) => h.score)) : null,
      check: !!body.check,
    }),
    signal,
  });
  if (!res.ok || !res.body) throw new ApiError(res.status, await detail(res));
  return readAnswerStream(res.body, onDelta);
}

// ------------------------------------------------------------------ flashcards (study_store.py, in localStorage)
type Review = { card_id: number; reviewed: string; grade: number; interval: number; ef: number };
type Study = { next_id: number; cards: Card[]; reviews: Review[] };

let memory: Study = { next_id: 1, cards: [], reviews: [] };   // used when the browser blocks storage

function readStudy(): Study {
  try {
    const raw = localStorage.getItem(CARDS_KEY);
    if (raw) memory = JSON.parse(raw) as Study;
  } catch {
    /* blocked or damaged storage: keep this page's copy */
  }
  return memory;
}

function writeStudy(s: Study): void {
  memory = s;
  try {
    localStorage.setItem(CARDS_KEY, JSON.stringify(s));
  } catch {
    /* blocked storage: the cards last until the page is closed */
  }
}

/** A local date, like Python's date.today(): toISOString() is UTC, a day behind in the early morning in India. */
function dateIn(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

type NewCard = Pick<Card, "front" | "back" | "file_name" | "page" | "doc_id" | "chunk_id" | "unit"> & { image_url: string | null; origin: string };

/** add_cards(): same front, file and page as an existing card = skipped. Returns the added cards. */
function addCards(drafts: NewCard[]): Card[] {
  const s = readStudy();
  const added: Card[] = [];
  for (const d of drafts) {
    const front = d.front.trim();
    if (s.cards.some((c) => c.front === front && c.file_name === d.file_name && c.page === d.page)) continue;
    const card: Card = { ...d, card_id: s.next_id++, front, back: d.back.trim(), due: dateIn(0), ef: 2.5, interval: 0, reps: 0, lapses: 0 };
    s.cards.push(card);
    added.push(card);
  }
  writeStudy(s);
  return added;
}

function dueCards(limit: number, units: string[]): Due {
  const today = dateIn(0);
  const s = readStudy();
  const due = s.cards.filter((c) => c.due <= today);
  const cards = due
    .filter((c) => !units.length || units.includes(c.unit ?? ""))
    .sort((a, b) => a.due.localeCompare(b.due) || a.card_id - b.card_id)
    .slice(0, limit);
  return { today, cards, stats: { cards: s.cards.length, due_today: due.length, reviews: s.reviews.length } };
}

function review(cardId: number, grade: number): Card {
  const s = readStudy();
  const card = s.cards.find((c) => c.card_id === cardId);
  if (!card) throw new ApiError(404, `no flashcard with id ${cardId}`);
  if (!Number.isInteger(grade) || grade < 0 || grade > 5) throw new ApiError(422, `grade must be 0..5, got ${grade}`);
  const [ef, interval, reps] = sm2(card.ef, card.interval, card.reps, grade);
  Object.assign(card, { ef, interval, reps, lapses: card.lapses + (grade < 3 ? 1 : 0), due: dateIn(interval) });
  s.reviews.push({ card_id: cardId, reviewed: dateIn(0), grade, interval, ef });
  writeStudy(s);
  return card;
}

async function fromQuiz(q: QuizQuestion): Promise<{ card: Card; created: boolean }> {
  if (q.options.length !== 4) throw new ApiError(422, "a quiz question has exactly 4 options");
  const { source } = q;
  const docs = await fetchOk("/demo/docs.json").then((r) => r.json() as Promise<DocumentRow[]>);
  const [card] = addCards([{
    front: q.question,
    back: `${q.options[q.answer]}. ${q.explanation}`,
    file_name: source.file_name,
    page: source.page,
    doc_id: source.doc_id,
    chunk_id: source.chunk_id,
    unit: docs.find((d) => d.doc_id === source.doc_id)?.unit ?? null,
    image_url: source.image_url,
    origin: "quiz",
  }]);
  if (card) return { card, created: true };
  const front = q.question.trim();
  const existing = readStudy().cards.find((c) => c.front === front && c.file_name === source.file_name && c.page === source.page);
  return { card: existing as Card, created: false };
}

async function generateCards(body: unknown) {
  const r = await server<{ cards: Omit<NewCard, "origin">[]; rejected: string[] }>("/api/demo/flashcards", body);
  const created = addCards(r.cards.map((c) => ({ ...c, origin: "generated" })));
  return { created, skipped_duplicates: r.cards.length - created.length, rejected: r.rejected };
}

// ------------------------------------------------------------------ the routes of api.py that the pages call
async function route(path: string, init?: RequestInit): Promise<unknown> {
  const url = new URL(path, "http://demo");
  const call = `${init?.method ?? "GET"} ${url.pathname}`;
  const body = typeof init?.body === "string" ? JSON.parse(init.body) : undefined;
  if (call === "GET /health") return server("/api/demo/health");
  if (call === "GET /documents") {
    if (location.pathname.startsWith("/ask")) warmUp();
    return (await fetchOk("/demo/docs.json")).json();
  }
  if (call === "POST /documents" || call.startsWith("DELETE /documents/")) throw new ApiError(403, DEMO_OFF);
  if (call === "POST /quiz") return server("/api/demo/quiz", body);
  if (call === "POST /flashcards/generate") return generateCards(body);
  if (call === "POST /flashcards/from-quiz") return fromQuiz(body as QuizQuestion);
  if (call === "GET /flashcards/due") return dueCards(Number(url.searchParams.get("limit") ?? 20), url.searchParams.getAll("unit"));
  const reviewed = call.match(/^POST \/flashcards\/(\d+)\/review$/);
  if (reviewed) return review(Number(reviewed[1]), body.grade);
  throw new ApiError(404, `${call} is not available in the online demo`);
}

export const demoRequest = <T>(path: string, init?: RequestInit) => route(path, init) as Promise<T>;
