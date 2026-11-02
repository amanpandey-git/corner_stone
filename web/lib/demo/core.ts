// Online demo (NEXT_PUBLIC_DEMO=1): logic shared by the browser and the Next.js server routes.
// Each function is a line-by-line port of the Python module named beside it, so the online demo
// behaves like the evaluated system: answer.py, citations.py, dedup.py, quiz.py, flashcards.py, srs.py.

// ------------------------------------------------------------------ exported data (web/scripts/export_demo.py)
export type ChunkRec = {
  id: number;
  doc_id: number;
  file_name: string;
  unit: string | null;
  page_start: number | null;
  page_end: number | null;
  section: string | null;
  chunk_index: number;
  token_count: number;
  text: string;
  image: string | null;
};

export type ModeCfg = { max_tokens: number; instruction: string };

export type DemoMeta = {
  exported_at: string;
  schema_version: number;
  n_chunks: number;
  dim: number;
  embedding: { model_name: string; query_prefix: string };
  prompts: { answer_system: string; quiz_system: string; cards_system: string; judge_system: string; not_in_notes: string };
  answer: { k: number; min_vector_score: number; judge_max_tokens: number; check_citations: boolean; modes: Record<string, ModeCfg> };
  llm: {
    temperature: number;
    max_retries: number;
    backoff_s: number;
    max_backoff_s: number;
    groq: { model: string; extra: Record<string, unknown> };
    groq_judge: { model: string; extra: Record<string, unknown> };
  };
  quiz: { min_tokens: number; max_sources: number; max_questions: number; max_attempts: number; max_tokens: number };
  flashcards: { max_cards: number; max_tokens: number };
  retrieval: { candidates: number; collapse: boolean };
  dedup: { result_jaccard: number };
  search: { max_query_chars: number; snippet_chars: number };
  self_check: { query: string; top_ids: number[]; top_scores: number[] };
};

export const MODES = ["concise", "detailed", "2-mark", "5-mark", "10-mark"];
export const NOT_IN_NOTES = "Not in your notes.";
export const NOT_IN_NOTES_TOKEN = "NOT_IN_NOTES";
export const DEMO_OFF =
  "The online demo runs on the seven sample lecture decks, so uploading and deleting notes is turned off. " +
  "Run Synapse on your own computer to add your notes.";

/** Source.label() in answer.py: 'Unit 3_Memory management, p.23' (or pp.9-10). */
export function label(c: Pick<ChunkRec, "file_name" | "page_start" | "page_end">): string {
  const stem = c.file_name.replace(/\.[^.\\/]*$/, "");
  if (c.page_start === null) return stem;
  if (c.page_end && c.page_end !== c.page_start) return `${stem}, pp.${c.page_start}-${c.page_end}`;
  return `${stem}, p.${c.page_start}`;
}

/** Python str.splitlines() line boundaries. */
const splitLines = (t: string) => t.split(/\r\n|[\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]/);
const words = (t: string) => t.split(/\s+/).filter(Boolean);

// ------------------------------------------------------------------ dedup.py: collapse near-identical results
export function pageSignature(text: string): Set<string> {
  // Python's \w is Unicode-aware; the constructor form keeps the u flag out of TypeScript's ES2017 target check
  const w = text.toLowerCase().match(new RegExp("[\\p{L}\\p{N}_]+", "gu")) ?? [];
  if (w.length < 3) return w.length ? new Set([w.join(" ")]) : new Set();
  const out = new Set<string>();
  for (let i = 0; i + 2 < w.length; i++) out.add(`${w[i]} ${w[i + 1]} ${w[i + 2]}`);
  return out;
}

export function jaccard(a: Set<string>, b: Set<string>): number {
  if (!a.size || !b.size) return 0;
  let inter = 0;
  for (const x of a) if (b.has(x)) inter++;
  return inter / (a.size + b.size - inter);
}

/** Keep the first of any group of results whose texts overlap at Jaccard >= threshold (order kept). */
export function collapse<T extends { chunk: ChunkRec }>(results: T[], threshold: number): T[] {
  const kept: [T, Set<string>][] = [];
  for (const r of results) {
    const sig = pageSignature(r.chunk.text);
    if (!kept.some(([, s]) => jaccard(sig, s) >= threshold)) kept.push([r, sig]);
  }
  return kept.map(([r]) => r);
}

// ------------------------------------------------------------------ citations.py
const MAX_RANGE = 20;
const REF_SRC = String.raw`\[\s*\d+(?:\s*[,\-–]\s*\d+)*\s*\]`;
const refAll = () => new RegExp(REF_SRC, "g");
const endAll = () => new RegExp(String.raw`[.!?](?:\s*` + REF_SRC + String.raw`)*(?=\s|$)`, "g");
const BULLET = /^\s*(?:[-*•]|\d+[.)])\s+/;
const GAP =
  /\b(?:notes|sources|slides)\s+(?:do not|don't|does not|doesn't)\b|\bnot\s+(?:covered|mentioned|given|explained|described)\s+in\s+(?:the|your)\s+(?:notes|sources|slides)/i;

export type Citation = { sentence: string; refs: number[] };

/** '[1, 3-5]' -> [1, 3, 4, 5]; a backwards or huge range yields its two ends only. */
function numbers(group: string): number[] {
  const out: number[] = [];
  for (let part of group.replace(/^[[\] ]+|[[\] ]+$/g, "").split(",")) {
    part = part.trim().replace(/–/g, "-");
    if (part.includes("-")) {
      const [a, b] = part.split("-").slice(0, 2).map((x) => parseInt(x.trim(), 10));
      if (b - a >= 0 && b - a <= MAX_RANGE) for (let i = a; i <= b; i++) out.push(i);
      else out.push(a, b);
    } else if (part) out.push(parseInt(part, 10));
  }
  return out;
}

export function splitSentences(text: string): string[] {
  const out: string[] = [];
  for (const line of splitLines(text)) {
    let pos = 0;
    for (const m of line.matchAll(endAll())) {
      const end = (m.index ?? 0) + m[0].length;
      out.push(line.slice(pos, end).trim());
      pos = end;
    }
    out.push(line.slice(pos).trim());
  }
  return out.filter(Boolean);
}

function isFactual(sentence: string): boolean {
  const s = sentence.replace(BULLET, "").trim().replace(/^[*_]+|[*_]+$/g, "").trim();
  if (!s || s === NOT_IN_NOTES_TOKEN || sentence.trimStart().startsWith("#")) return false;
  if (s.endsWith(":") || GAP.test(s)) return false;
  return words(s).length >= 4;
}

/** (citations, uncited factual sentences, invalid reference numbers). */
export function parseCitations(text: string, nSources: number): [Citation[], string[], number[]] {
  const citations: Citation[] = [];
  const uncited: string[] = [];
  const invalid = new Set<number>();
  for (const sentence of splitSentences(text)) {
    const refs: number[] = [];
    for (const g of sentence.match(refAll()) ?? []) {
      for (const n of numbers(g)) {
        if (n >= 1 && n <= nSources) {
          if (!refs.includes(n)) refs.push(n);
        } else invalid.add(n);
      }
    }
    const bare = words(sentence.replace(refAll(), " ")).join(" ").replace(/\s+([.!?,;:])/g, "$1");
    if (refs.length) citations.push({ sentence: bare, refs });
    else if (isFactual(sentence)) uncited.push(bare);
  }
  return [citations, uncited, [...invalid].sort((a, b) => a - b)];
}

export function stripInvalidRefs(text: string, nSources: number): string {
  const out = text.replace(refAll(), (g) => {
    const keep: number[] = [];
    for (const n of numbers(g)) if (n >= 1 && n <= nSources && !keep.includes(n)) keep.push(n);
    return keep.length ? `[${keep.join(", ")}]` : "";
  });
  return out.replace(/[ \t]{2,}/g, " ").replace(/[ \t]+([.!?,;:])/g, "$1");
}

export function buildJudgePrompt(citations: Citation[], texts: Map<number, string>): string {
  return citations
    .map((c, i) => {
      const cited = c.refs.map((n) => `  [${n}] ${words(texts.get(n) ?? "").join(" ")}`).join("\n");
      return `Claim ${i + 1}: ${c.sentence}\nCited slides:\n${cited}`;
    })
    .join("\n\n");
}

/** 0-based indexes of unsupported claims, or null if the reply is not the expected JSON. */
export function parseJudgeReply(reply: string, nClaims: number): number[] | null {
  const m = reply.match(/\{[\s\S]*\}/);
  if (!m) return null;
  try {
    const bad = JSON.parse(m[0]).unsupported;
    if (!Array.isArray(bad) || !bad.every((x) => Number.isInteger(x))) return null;
    return [...new Set(bad.filter((x: number) => x >= 1 && x <= nClaims).map((x: number) => x - 1))].sort((a, b) => a - b);
  } catch {
    return null;
  }
}

// ------------------------------------------------------------------ answer.py
export type Source = { n: number; chunk: ChunkRec };

export function buildPrompt(question: string, sources: Source[], mode: string, meta: DemoMeta): [string, string] {
  const system = meta.prompts.answer_system.replace("{instruction}", () => meta.answer.modes[mode].instruction);
  const blocks = sources.map((s) => {
    const head = `[${s.n}] ${label(s.chunk)}` + (s.chunk.section ? ` - ${s.chunk.section}` : "");
    return `${head}\n${s.chunk.text.trim()}`;
  });
  return [system, "Sources:\n\n" + blocks.join("\n\n") + `\n\nQuestion: ${question.trim()}`];
}

const LENTICULAR = /【\s*(\d+(?:\s*[,\-–]\s*\d+)*)[^】]*】/g;

/** NFKC, and gpt-oss's 【1】 / 【1†L3】 citation brackets become [1]. */
export function normalise(text: string): string {
  return text.normalize("NFKC").replace(LENTICULAR, (_, g: string) => `[${g}]`).trim();
}

export type Finalised = {
  text: string;
  abstained: boolean;
  abstain_reason: string | null;
  citations: Citation[];
  uncited_sentences: string[];
  invalid_refs: number[];
};

export function finalise(raw: string, nSources: number): Finalised {
  let text = normalise(raw);
  if (text.toUpperCase().startsWith(NOT_IN_NOTES_TOKEN) || (text.includes(NOT_IN_NOTES_TOKEN) && !text.includes("[")))
    return { text: NOT_IN_NOTES, abstained: true, abstain_reason: "model", citations: [], uncited_sentences: [], invalid_refs: [] };
  text = splitLines(text).map((l) => l.replaceAll(NOT_IN_NOTES_TOKEN, "").trimEnd()).join("\n").trim();
  const [citations, uncited, invalid] = parseCitations(text, nSources);
  if (!citations.length)
    return { text: NOT_IN_NOTES, abstained: true, abstain_reason: "no_citations", citations: [], uncited_sentences: uncited, invalid_refs: invalid };
  return { text: stripInvalidRefs(text, nSources), abstained: false, abstain_reason: null, citations, uncited_sentences: uncited, invalid_refs: invalid };
}

// ------------------------------------------------------------------ srs.py (SM-2, Wozniak 1990)
export function sm2(ef: number, interval: number, reps: number, grade: number): [number, number, number] {
  if (!(grade >= 0 && grade <= 5)) throw new Error(`grade must be 0..5, got ${grade}`);
  if (grade < 3) {
    reps = 0;
    interval = 1;
  } else {
    reps += 1;
    interval = reps === 1 ? 1 : reps === 2 ? 6 : pyRound(interval * ef);
  }
  ef = Math.max(1.3, ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)));
  return [ef, interval, reps];
}

/** Python's round(): halves go to the even neighbour. */
function pyRound(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (Math.abs(d - 0.5) < 1e-9) return f % 2 === 0 ? f : f + 1;
  return Math.round(x);
}

// ------------------------------------------------------------------ quiz.py / flashcards.py
/** Seeded generator (mulberry32) for picking slides; the Python version uses random.Random(seed). */
export function seeded(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Up to quiz.max_sources slides with enough text, spread evenly through the selected documents. */
export function pickSlides(chunks: ChunkRec[], units: string[] | undefined, meta: DemoMeta, seed: number): Source[] {
  const pool = chunks
    .filter((c) => (!units?.length || units.includes(c.unit ?? "")) && c.token_count >= meta.quiz.min_tokens)
    .sort((a, b) => a.doc_id - b.doc_id || (a.page_start ?? 0) - (b.page_start ?? 0) || a.chunk_index - b.chunk_index);
  if (!pool.length) throw new Error(`no slides with enough text match ${units?.join(", ") || "the index"}`);
  const m = Math.min(pool.length, meta.quiz.max_sources);
  const step = pool.length / m;
  const offset = seeded(seed)() * step;
  return Array.from({ length: m }, (_, i) => ({ n: i + 1, chunk: pool[Math.min(Math.floor(offset + i * step), pool.length - 1)] }));
}

export function sourcesBlock(sources: Source[]): string {
  return sources
    .map((s) => `[${s.n}] ${label(s.chunk)}` + (s.chunk.section ? ` - ${s.chunk.section}` : "") + `\n${s.chunk.text.trim()}`)
    .join("\n\n");
}

/** The list under `key` in the first JSON object of the reply; null if there is no such list. */
export function jsonItems(reply: string, key: string): unknown[] | null {
  const m = normalise(reply).match(/\{[\s\S]*\}/);
  if (!m) return null;
  try {
    const data = JSON.parse(m[0]);
    const items = data && typeof data === "object" && !Array.isArray(data) ? data[key] : null;
    return Array.isArray(items) ? items : null;
  } catch {
    return null;
  }
}

/** pydantic int in lax mode: an integer, or a string / float holding an integer. */
function asInt(v: unknown): number | null {
  if (typeof v === "boolean") return v ? 1 : 0;
  if (typeof v === "number" && Number.isInteger(v)) return v;
  if (typeof v === "string" && /^\s*[-+]?\d+\s*$/.test(v)) return parseInt(v, 10);
  return null;
}

export type Mcq = { question: string; options: string[]; answer: number; explanation: string; source: number };

/** quiz.MCQ validation: returns the cleaned question or the reasons it was rejected. */
export function validateMcq(item: unknown): Mcq | string {
  if (!item || typeof item !== "object") return "not an object";
  const o = item as Record<string, unknown>;
  const errs: string[] = [];
  const str = (k: string) => {
    if (typeof o[k] !== "string") errs.push(`${k}: Input should be a valid string`);
    else if (!(o[k] as string).trim()) errs.push(`${k}: Value error, must not be empty`);
    return typeof o[k] === "string" ? (o[k] as string).trim() : "";
  };
  const question = str("question");
  const explanation = str("explanation");
  let options: string[] = [];
  if (!Array.isArray(o.options) || !o.options.every((x) => typeof x === "string")) errs.push("options: Input should be a valid list of strings");
  else {
    options = (o.options as string[]).map((x) => x.trim());
    if (options.length !== 4) errs.push(`options: Value error, needs exactly 4 options, got ${options.length}`);
    else if (options.some((x) => !x)) errs.push("options: Value error, an option is empty");
    else if (new Set(options.map((x) => x.toLowerCase().split(/\s+/).filter(Boolean).join(" "))).size !== 4)
      errs.push("options: Value error, options are not distinct");
    else if (options.some((x) => /\b(all|none) of the above\b/i.test(x))) errs.push("options: Value error, uses 'all/none of the above'");
  }
  const answer = asInt(o.answer);
  if (answer === null) errs.push("answer: Input should be a valid integer");
  else if (answer < 0 || answer > 3) errs.push(`answer: Value error, answer index ${answer} is not 0..3`);
  const source = asInt(o.source);
  if (source === null) errs.push("source: Input should be a valid integer");
  return errs.length ? errs.join("; ") : { question, options, answer: answer as number, explanation, source: source as number };
}

export type CardDraft = { front: string; back: string; source: number };

export function validateCard(item: unknown): CardDraft | string {
  if (!item || typeof item !== "object") return "not an object";
  const o = item as Record<string, unknown>;
  const errs: string[] = [];
  for (const k of ["front", "back"]) {
    if (typeof o[k] !== "string") errs.push(`${k}: Input should be a valid string`);
    else if (!(o[k] as string).trim()) errs.push(`${k}: Value error, must not be empty`);
  }
  const source = asInt(o.source);
  if (source === null) errs.push("source: Input should be a valid integer");
  return errs.length ? errs.join("; ") : { front: (o.front as string).trim(), back: (o.back as string).trim(), source: source as number };
}
