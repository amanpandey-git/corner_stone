"use client";

import { ChevronDown, SearchX, Send } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import CitedText from "@/components/CitedText";
import Notice from "@/components/Notice";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { Kbd } from "@/components/ui/Kbd";
import { Skeleton } from "@/components/ui/Skeleton";
import { SlideDialog, SlideDock, type Slide } from "@/components/ui/SlidePanel";
import { DEMO, getJSON, MODES, streamAsk, type Answer, type DocumentRow, type Mode, type Source } from "@/lib/api";
import { plural, splitLabel } from "@/lib/format";

const WHY: Record<string, string> = {
  retrieval: "Nothing in your notes is close to this question.",
  model: "The closest slides do not answer it.",
  no_citations: "The model's answer could not be tied to any slide.",
};

// Labels and length hints only; the mode values and their instructions are untouched.
const MODE_UI: Record<Mode, { label: string; hint: string }> = {
  concise: { label: "Concise", hint: "A direct answer in 2-4 sentences." },
  detailed: { label: "Detailed", hint: "Covers every relevant point in the slides." },
  "2-mark": { label: "2 marks", hint: "About 40-60 words: a definition plus one key point." },
  "5-mark": { label: "5 marks", hint: "About 150-250 words: an introduction, then 4-6 key points." },
  "10-mark": { label: "10 marks", hint: "About 400-600 words: an introduction, then the main points." },
};

const STARTERS = [
  { q: "Explain the SCAN disk scheduling algorithm with its advantages and disadvantages." },
  { q: "What is paging in memory management?" },
  { q: "Explain the access matrix model of protection." },
  { q: "How does TCP congestion control work?", note: "not in these notes" },
];

type Turn = {
  id: number;
  question: string;
  mode: Mode;
  unit: string;
  check: boolean;
  phase: "searching" | "writing" | "done" | "error";
  streamed: string;
  answer: Answer | null;
  error: unknown;
};

type Open = { turnId: number; n: number; focus: boolean };

const toSlide = (s: Source): Slide => ({ label: s.label, image_url: s.image_url, section: s.section, text: s.text, n: s.n });

function useDesktop() {
  return useSyncExternalStore(
    (notify) => {
      const m = matchMedia("(min-width: 1024px)");
      m.addEventListener("change", notify);
      return () => m.removeEventListener("change", notify);
    },
    () => matchMedia("(min-width: 1024px)").matches,
    () => false,
  );
}

/** 0-99 while the search model downloads, 100 when ready, null if it failed. Reports only; see lib/demo/client.ts. */
function useModelLoad() {
  const [percent, setPercent] = useState<number | null>(DEMO ? 0 : 100);
  useEffect(() => {
    if (!DEMO) return;
    const client = import("@/lib/demo/client");
    client.then(({ watchModelLoad }) => watchModelLoad(setPercent));
    return () => {
      client.then(({ watchModelLoad }) => watchModelLoad(null));
    };
  }, []);
  return percent;
}

/** Reads ?unit= from a Documents card. In its own Suspense, so the rest of the page can still be prerendered. */
function UnitFromUrl({ units, onUnit }: { units: string[]; onUnit: (u: string) => void }) {
  const wanted = useSearchParams().get("unit");
  useEffect(() => {
    if (wanted && units.includes(wanted)) onUnit(wanted);
  }, [wanted, units, onUnit]);
  return null;
}

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<Mode>("concise");
  const [unit, setUnit] = useState("");
  const [check, setCheck] = useState(false);
  const [units, setUnits] = useState<string[]>([]);
  const [docsError, setDocsError] = useState<unknown>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [open, setOpen] = useState<Open | null>(null);
  const abort = useRef<AbortController | null>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const nextId = useRef(1);
  const lastQuestion = useRef<HTMLDivElement>(null);
  const desktop = useDesktop();
  const percent = useModelLoad();

  const loadDocs = useCallback(() => {
    setDocsError(null);
    getJSON<DocumentRow[]>("/documents").then(
      (docs) => setUnits([...new Set(docs.map((d) => d.unit).filter((u): u is string => !!u))].sort()),
      (e) => setDocsError(e),
    );
  }, []);

  useEffect(() => {
    loadDocs();
    return () => abort.current?.abort();
  }, [loadDocs]);

  // Ctrl/Cmd+K focuses the question box from anywhere on the page.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        box.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const count = turns.length;
  useEffect(() => {
    if (count > 1) lastQuestion.current?.scrollIntoView({ block: "start" });
  }, [count]);

  const patch = (id: number, change: (t: Turn) => Partial<Turn>) =>
    setTurns((list) => list.map((t) => (t.id === id ? { ...t, ...change(t) } : t)));

  const busy = turns.some((t) => t.phase === "searching" || t.phase === "writing");

  async function run(t: Pick<Turn, "question" | "mode" | "unit" | "check">, retryId?: number) {
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    const id = retryId ?? nextId.current++;
    const fresh: Turn = { ...t, id, phase: "searching", streamed: "", answer: null, error: null };
    setTurns((list) => (retryId ? list.map((x) => (x.id === id ? fresh : x)) : [...list, fresh]));
    setOpen(null);
    try {
      const final = await streamAsk(
        { question: t.question, mode: t.mode, units: t.unit ? [t.unit] : undefined, check: t.check },
        (piece) => patch(id, (x) => ({ phase: "writing", streamed: x.streamed + piece })),
        ctrl.signal,
      );
      patch(id, () => ({ phase: "done", answer: final }));
      // On wide screens the first cited slide opens beside the answer, without taking focus from the question box.
      const first = final.abstained ? undefined : final.sources.find((s) => s.cited);
      if (first && matchMedia("(min-width: 1024px)").matches) setOpen({ turnId: id, n: first.n, focus: false });
    } catch (err) {
      if (!ctrl.signal.aborted) patch(id, () => ({ phase: "error", error: err }));
    }
  }

  function submit(text = question) {
    const q = text.trim();
    if (!q || busy) return;
    setQuestion("");
    run({ question: q, mode, unit, check });
    box.current?.focus();
  }

  // The slides that previous/next step through: the cited ones, or just the one opened if it was not cited.
  const openTurn = open && turns.find((t) => t.id === open.turnId);
  const openSources = openTurn?.answer?.sources ?? [];
  const cited = openSources.filter((s) => s.cited);
  const list = open && cited.some((s) => s.n === open.n) ? cited : openSources.filter((s) => s.n === open?.n);
  const slides = list.map(toSlide);
  const index = Math.max(0, list.findIndex((s) => s.n === open?.n));
  const panelProps = open && slides.length ? {
    slides,
    index,
    onIndex: (i: number) => setOpen({ ...open, n: list[i].n, focus: false }),
    onClose: () => setOpen(null),
  } : null;

  return (
    <div className="page pt-6 md:pt-10">
      <Suspense fallback={null}><UnitFromUrl units={units} onUnit={setUnit} /></Suspense>
      <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(22rem,28rem)] lg:items-start lg:gap-8">
        <div className="flex min-h-[calc(100dvh-13rem)] min-w-0 flex-col">
          <header className="ruled">
            <h1 className="text-h1">Ask your notes</h1>
            <p className="mt-1 text-ink-2">Each question is answered on its own, from your slides.</p>
          </header>

          {percent !== null && percent < 100 && <Warmup percent={percent} />}
          {docsError != null && <ErrorState className="mt-6" error={docsError} onRetry={loadDocs} />}

          <div className="mt-6 flex-1 space-y-10">
            {turns.length === 0 && <Starters onPick={submit} disabled={busy} />}
            {turns.map((t, i) => (
              <div key={t.id} ref={i === turns.length - 1 ? lastQuestion : undefined} className="scroll-mt-4 space-y-4">
                <TurnView
                  turn={t}
                  percent={percent}
                  openN={open?.turnId === t.id ? open.n : null}
                  onCite={(n, focus) => setOpen({ turnId: t.id, n, focus })}
                  onRetry={() => run(t, t.id)}
                  onRephrase={() => { setQuestion(t.question); box.current?.focus(); }}
                  onAllUnits={t.unit ? () => { setUnit(""); setQuestion(t.question); box.current?.focus(); } : undefined}
                />
              </div>
            ))}
          </div>

          <form
            onSubmit={(e) => { e.preventDefault(); submit(); }}
            className="sticky bottom-[4.25rem] z-20 mt-8 space-y-2 rounded-xl border bg-raised p-3 shadow-sheet md:bottom-4"
          >
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-small">
              <fieldset className="hidden rounded-md bg-sunk p-0.5 sm:flex">
                <legend className="sr-only">Answer as</legend>
                {MODES.map((m) => (
                  <label key={m} className={`inline-flex min-h-9 items-center rounded-[8px] px-2.5 has-focus-visible:outline-2 has-focus-visible:outline-ink ${mode === m ? "bg-marker font-semibold text-on-marker" : "text-ink-2 hover:text-ink"}`}>
                    <input type="radio" name="mode" value={m} checked={mode === m} onChange={() => setMode(m)} className="sr-only" />
                    {MODE_UI[m].label}
                  </label>
                ))}
              </fieldset>
              <label className="flex items-center gap-1.5 sm:hidden">
                <span className="sr-only">Answer as</span>
                <select value={mode} onChange={(e) => setMode(e.target.value as Mode)} className="min-h-11 rounded-md border border-rule-strong bg-raised px-2">
                  {MODES.map((m) => <option key={m} value={m}>{MODE_UI[m].label}</option>)}
                </select>
              </label>
              <label className="flex items-center gap-1.5 text-ink-2">
                <span className="sr-only sm:not-sr-only">Unit</span>
                <select aria-label="Unit" value={unit} onChange={(e) => setUnit(e.target.value)} className="min-h-11 rounded-md border border-rule-strong bg-raised px-2 text-ink sm:min-h-9">
                  <option value="">All units</option>
                  {units.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </label>
              <label className="flex min-h-11 items-center gap-2 text-ink-2 sm:min-h-9" title="A second model checks each cited sentence against its slide (slower, uses more AI quota)">
                <input type="checkbox" checked={check} onChange={(e) => setCheck(e.target.checked)} className="h-5 w-5 accent-[var(--ink)]" />
                Check citations
              </label>
            </div>
            <p className="hidden text-small text-ink-3 sm:block">{MODE_UI[mode].hint}</p>
            <div className="flex items-end gap-2">
              <label className="min-w-0 flex-1">
                <span className="sr-only">Your question</span>
                <textarea
                  ref={box}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
                  rows={1}
                  placeholder="Ask about your slides..."
                  className="block max-h-40 min-h-12 w-full resize-none rounded-md border border-rule-strong bg-paper px-3 py-2.5 placeholder:text-ink-3 field-sizing-content"
                />
              </label>
              <Button type="submit" size="lg" disabled={!question.trim() || busy} aria-label={busy ? "Answering" : "Ask"}>
                <Send size={18} strokeWidth={1.75} aria-hidden />
                <span className="hidden sm:inline">{busy ? "Answering..." : "Ask"}</span>
              </Button>
            </div>
            <p className="hidden items-center gap-1.5 text-small text-ink-3 md:flex">
              <Kbd>Ctrl K</Kbd> to focus <span aria-hidden>·</span> <Kbd>Enter</Kbd> to send <span aria-hidden>·</span> <Kbd>Shift Enter</Kbd> for a new line
            </p>
          </form>
        </div>

        {/* The margin: reserved on wide screens, so opening a slide never moves the answer. */}
        <div className="hidden lg:sticky lg:top-6 lg:block">
          {desktop && panelProps ? (
            <SlideDock key={open?.turnId} {...panelProps} takeFocus={open?.focus} />
          ) : (
            <div className="rounded-xl border border-dashed border-rule-strong p-6 text-small text-ink-3">
              The margin. Press a yellow number in an answer and its slide opens here, beside the sentence it supports.
            </div>
          )}
        </div>
      </div>
      {!desktop && panelProps && <SlideDialog {...panelProps} />}
    </div>
  );
}

/** First visit: the search model downloads into the browser. The percent is real, from transformers.js. */
function Warmup({ percent }: { percent: number }) {
  const shown = Math.round(percent);
  return (
    <div role="status" className="mt-6 rounded-md bg-sunk p-4">
      <div className="flex items-baseline justify-between gap-4">
        <p className="font-semibold">Preparing search in your browser</p>
        <p className="font-mono text-mono text-ink-2 tabular-nums">{shown > 0 ? `${shown}%` : "starting"}</p>
      </div>
      <div role="progressbar" aria-label="Search model download" aria-valuemin={0} aria-valuemax={100} aria-valuenow={shown} className="mt-2 h-2 overflow-hidden rounded-full bg-rule">
        <div className="h-full origin-left rounded-full bg-marker transition-transform duration-200" style={{ transform: `scaleX(${shown / 100})` }} />
      </div>
      <p className="mt-2 text-small text-ink-2">The first visit downloads a 34 MB model; later visits are much faster. You can type your question now.</p>
    </div>
  );
}

function Starters({ onPick, disabled }: { onPick: (q: string) => void; disabled: boolean }) {
  return (
    <section aria-labelledby="starters" className="ruled space-y-3">
      <h2 id="starters" className="font-sans text-h3">Try one</h2>
      <p className="max-w-[56ch] text-ink-2">Answers come only from the 7 decks, with the slide to prove it.</p>
      <ul className="space-y-2">
        {STARTERS.map((s) => (
          <li key={s.q}>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onPick(s.q)}
              className="min-h-11 w-full rounded-md border border-rule-strong bg-raised px-3 py-2 text-left text-small hover:bg-sunk disabled:opacity-50 md:text-body"
            >
              {s.q}
              {s.note && <span className="ml-2 font-mono text-mono text-ink-3">{s.note}</span>}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function TurnView({ turn, percent, openN, onCite, onRetry, onRephrase, onAllUnits }: {
  turn: Turn;
  percent: number | null;
  openN: number | null;
  onCite: (n: number, focus: boolean) => void;
  onRetry: () => void;
  onRephrase: () => void;
  onAllUnits?: () => void;
}) {
  const { answer } = turn;
  const status =
    turn.phase === "searching"
      ? percent !== null && percent < 100 ? `Waiting for the search model, ${Math.round(percent)}%` : "Searching slides"
      : turn.phase === "writing" ? "Writing" : null;
  return (
    <>
      <div className="ml-auto w-fit max-w-[88%] rounded-lg bg-sunk px-4 py-2.5">
        <p className="font-semibold">{turn.question}</p>
        <p className="mt-1 flex flex-wrap items-center gap-1.5">
          <Badge>{MODE_UI[turn.mode].label}</Badge>
          {turn.unit && <Badge>{turn.unit}</Badge>}
        </p>
      </div>

      {/* Announced once when finished, not on every word. */}
      <p role="status" className="sr-only">{status ?? (turn.phase === "done" ? "Answer ready" : "")}</p>

      {turn.phase === "searching" && (
        <div className="ruled space-y-2" aria-hidden>
          <p className="text-small text-ink-3">{status}</p>
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      )}

      {turn.phase === "writing" && (
        <div className="ruled">
          <p className="mb-2 text-small text-ink-3">{status}</p>
          <CitedText text={turn.streamed} live />
        </div>
      )}

      {turn.phase === "error" && <ErrorState error={turn.error} onRetry={onRetry} />}

      {turn.phase === "done" && answer && (answer.abstained
        ? <NotInNotes answer={answer} onRephrase={onRephrase} onAllUnits={onAllUnits} />
        : <AnswerView answer={answer} check={turn.check} openN={openN} onCite={onCite} />)}
    </>
  );
}

/** The product's proudest behaviour gets a proper state. The words themselves come straight from the answer. */
function NotInNotes({ answer, onRephrase, onAllUnits }: { answer: Answer; onRephrase: () => void; onAllUnits?: () => void }) {
  return (
    <section className="ruled">
      <p className="flex items-start gap-3 font-display text-h1">
        <SearchX size={32} strokeWidth={1.5} aria-hidden className="mt-1.5 hidden shrink-0 text-ink-3 sm:block" />
        {answer.text}
      </p>
      <p className="mt-3 max-w-[56ch] text-ink-2">
        {WHY[answer.abstain_reason ?? ""] ?? answer.abstain_reason} Synapse would rather say so than guess.
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button variant="secondary" size="sm" onClick={onRephrase}>Rephrase it</Button>
        {onAllUnits && <Button variant="secondary" size="sm" onClick={onAllUnits}>Search all units</Button>}
        <Link href="/documents" className="inline-flex min-h-11 items-center px-2 text-small font-semibold underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
          See what is in the notes
        </Link>
      </div>
    </section>
  );
}

function AnswerView({ answer, check, openN, onCite }: {
  answer: Answer;
  check: boolean;
  openN: number | null;
  onCite: (n: number, focus: boolean) => void;
}) {
  const citedCount = answer.sources.filter((s) => s.cited).length;
  return (
    <div className="space-y-4">
      <div className="ruled">
        <CitedText
          text={answer.text}
          onCite={(n) => onCite(n, true)}
          labelFor={(n) => answer.sources.find((s) => s.n === n)?.label}
        />
      </div>

      {/* Honesty notices stay visible: restyled, never hidden. */}
      {answer.uncited_sentences.length > 0 && (
        <Notice kind="warn">Not backed by a citation: {answer.uncited_sentences.join(" | ")}</Notice>
      )}
      {answer.invalid_refs.length > 0 && (
        <Notice kind="warn">Removed citations to sources that do not exist: {answer.invalid_refs.join(", ")}</Notice>
      )}
      {answer.unsupported && answer.unsupported.length > 0 && (
        <Notice kind="warn">
          The checker found these claims unsupported by their slide:{" "}
          {answer.unsupported.map((i) => answer.citations[i]?.sentence).join(" | ")}
        </Notice>
      )}
      {check && answer.unsupported === null && <p className="text-small text-ink-3">Citations could not be checked this time.</p>}

      <details className="group rounded-md border bg-raised">
        <summary className="flex min-h-11 list-none items-center justify-between gap-3 px-3 py-2 text-small font-semibold [&::-webkit-details-marker]:hidden">
          {plural(answer.sources.length, "slide")} searched · {citedCount} cited
          <ChevronDown size={16} strokeWidth={1.5} aria-hidden className="shrink-0 transition-transform duration-200 group-open:rotate-180" />
        </summary>
        <ul className="divide-y border-t">
          {answer.sources.map((s) => {
            const { deck, page } = splitLabel(s.label);
            return (
              <li key={s.n}>
                <button
                  type="button"
                  onClick={() => onCite(s.n, true)}
                  aria-current={openN === s.n ? "true" : undefined}
                  className={`block w-full px-3 py-2.5 text-left hover:bg-sunk ${openN === s.n ? "bg-sunk" : ""}`}
                >
                  <span className="flex flex-wrap items-center gap-2 text-small">
                    <Badge tone={s.cited ? "marker" : "neutral"}>{s.n}</Badge>
                    <span className="font-semibold">{s.section ?? deck}</span>
                    {!s.cited && <span className="text-ink-3">not cited</span>}
                  </span>
                  <span className="mt-0.5 block text-small text-ink-3">{deck}{page && <span className="font-mono text-mono"> · {page}</span>}</span>
                  <span className="mt-1 line-clamp-2 block text-small text-ink-2">{s.text}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </details>

      <details className="text-small text-ink-3">
        <summary className="inline-flex min-h-11 cursor-pointer items-center">Details</summary>
        <p>
          {answer.provider} {answer.model} · first words after {Math.round(answer.ttft_ms ?? 0)} ms
          {answer.cached ? " · from cache" : ""}
        </p>
      </details>
    </div>
  );
}
