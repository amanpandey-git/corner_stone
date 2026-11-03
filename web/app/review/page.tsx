"use client";

import { Sparkles } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card as Surface } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Kbd } from "@/components/ui/Kbd";
import { Skeleton } from "@/components/ui/Skeleton";
import { SlideDialog, type Slide } from "@/components/ui/SlidePanel";
import { DEMO, getJSON, postJSON, type Card, type DocumentRow, type Due } from "@/lib/api";
import { sm2 } from "@/lib/demo/core";
import { deckName, plural } from "@/lib/format";

// The same grades as the Streamlit page. Grading still runs where it always did (the API, or the demo's store);
// sm2() is only called here to show what each button would do, with the same numbers it will really use.
const GRADES = [
  { key: "1", label: "Again", grade: 1, tone: "text-wrong" },
  { key: "2", label: "Hard", grade: 3, tone: "text-warn" },
  { key: "3", label: "Good", grade: 4, tone: "text-correct" },
  { key: "4", label: "Easy", grade: 5, tone: "text-ink" },
];

const days = (n: number) => (n === 1 ? "1 day" : `${n} days`);

export default function ReviewPage() {
  const [units, setUnits] = useState<string[]>([]);
  const [unit, setUnit] = useState("");
  const [due, setDue] = useState<Due | null>(null);
  const [shown, setShown] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [slide, setSlide] = useState<Slide | null>(null);
  const back = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    const q = unit ? `&unit=${encodeURIComponent(unit)}` : "";
    getJSON<Due>(`/flashcards/due?limit=50${q}`).then(
      (d) => { setDue(d); setShown(false); setError(null); },
      (e) => setError(e),
    );
  }, [unit]);

  useEffect(load, [load]);
  useEffect(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (docs) => setUnits([...new Set(docs.map((d) => d.unit).filter((u): u is string => !!u))].sort()),
      (e) => setError(e),
    );
  }, []);

  const card = due?.cards[0];

  const grade = useCallback(async (c: Card, g: number) => {
    setBusy(true);
    try {
      const next = await postJSON<Card>(`/flashcards/${c.card_id}/review`, { grade: g });
      setNote(`Next review of that card: ${next.due}, in ${days(next.interval)}.`);
      load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }, [load]);

  async function generate() {
    setGenerating(true);
    setError(null);
    try {
      const r = await postJSON<{ created: Card[]; skipped_duplicates: number; rejected: unknown[] }>(
        "/flashcards/generate", { units: unit ? [unit] : undefined, n: 10, seed: Date.now() % 100000 });
      setNote(`${plural(r.created.length, "card")} created` + (r.skipped_duplicates ? `, ${r.skipped_duplicates} already existed` : "") + ".");
      load();
    } catch (e) {
      setError(e);
    } finally {
      setGenerating(false);
    }
  }

  // Space flips; 1 to 4 grade once the answer shows. Never while typing, on a focused control, or with a slide open.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (slide || !card || busy || e.ctrlKey || e.metaKey || e.altKey) return;
      const tag = (e.target as HTMLElement).tagName;
      if (["INPUT", "SELECT", "TEXTAREA", "BUTTON", "A", "SUMMARY"].includes(tag)) return;
      if (e.key === " ") {
        e.preventDefault();
        setShown((s) => !s);
      } else if (shown) {
        const g = GRADES.find((x) => x.key === e.key);
        if (g) grade(card, g.grade);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [slide, card, busy, shown, grade]);

  useEffect(() => {
    if (shown) back.current?.focus({ preventScroll: true });
  }, [shown]);

  return (
    <div className="page max-w-3xl pt-6 md:pt-10">
      <header className="ruled flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
        <div>
          <h1 className="text-h1">Flashcards</h1>
          <p className="mt-1 text-ink-2">
            {due ? <><strong className="font-bold text-ink">{due.stats.due_today} due today</strong> · {plural(due.stats.cards, "card")} · {plural(due.stats.reviews, "review")} so far</> : "Spaced repetition from your slides."}
          </p>
        </div>
      </header>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-small text-ink-2">
          Unit
          <select value={unit} onChange={(e) => setUnit(e.target.value)} className="min-h-11 rounded-md border border-rule-strong bg-raised px-2 text-body text-ink">
            <option value="">All units</option>
            {units.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </label>
        {(card || generating) && (
          <Button variant="secondary" size="sm" onClick={generate} disabled={generating || busy} title="Uses the AI quota">
            <Sparkles size={16} strokeWidth={1.5} aria-hidden />
            {generating ? "Writing cards..." : "Generate 10 cards"}
          </Button>
        )}
      </div>

      {error != null && <ErrorState className="mt-4" error={error} onRetry={load} />}
      {note && <p role="status" className="mt-4 rounded-md bg-sunk px-3 py-2 text-small text-ink-2">{note}</p>}

      <div className="mt-6">
        {!due && !error && (
          <Surface className="space-y-3 p-6" aria-hidden>
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-8 w-4/5" />
            <Skeleton className="h-8 w-3/5" />
          </Surface>
        )}

        {due && !card && !generating && (
          <EmptyState
            title={due.stats.cards ? "Nothing more due" : "No cards yet"}
            action={<>
              <Button onClick={generate} disabled={generating}>
                <Sparkles size={18} strokeWidth={1.5} aria-hidden />
                Generate 10 cards
              </Button>
              <ButtonLink href="/quiz" variant="secondary">Take a quiz</ButtonLink>
            </>}
          >
            {due.stats.cards
              ? `No cards are due${unit ? ` in ${unit}` : ""} right now. Come back when they are, or add more.`
              : "Generate cards from your slides, which uses the AI quota, or take a quiz: a wrong answer can become a card."}
          </EmptyState>
        )}

        {generating && !card && (
          <Surface className="space-y-3 p-6" role="status" aria-label="Writing cards">
            <p className="text-small text-ink-3">Writing cards from your slides...</p>
            <Skeleton className="h-8 w-4/5" />
            <Skeleton className="h-8 w-3/5" />
          </Surface>
        )}

        {card && (
          <>
            <div className="flip" data-flipped={shown}>
              <div className="flip-inner">
                <Surface inert={shown} className="flex min-h-72 flex-col p-6 shadow-sheet md:p-8">
                  <CardTag card={card} />
                  <p className="my-auto py-6 font-display text-h2 font-semibold">{card.front}</p>
                  <div className="flex flex-wrap items-center gap-3">
                    <Button onClick={() => setShown(true)}>Show answer</Button>
                    <span className="hidden items-center gap-1.5 text-small text-ink-3 md:inline-flex"><Kbd>Space</Kbd> to flip</span>
                  </div>
                </Surface>

                <Surface inert={!shown} className="flip-back flex min-h-72 flex-col p-6 shadow-sheet md:p-8">
                  <CardTag card={card} />
                  <div ref={back} tabIndex={-1} className="my-auto py-6 focus:outline-none">
                    <p className="text-small text-ink-3">{card.front}</p>
                    <p className="mt-3 border-t pt-3 text-lede">{card.back}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSlide({ label: `${card.file_name}, p.${card.page ?? "?"}`, image_url: card.image_url ?? null })}
                    className="inline-flex min-h-11 w-fit items-center text-left text-small text-accent-ink underline-offset-4 hover:underline"
                  >
                    Source: {deckName(card.file_name)}{card.page != null && <span className="ml-1 font-mono text-mono">· p.{card.page}</span>}
                  </button>
                </Surface>
              </div>
            </div>

            {/* Kept in the layout before the flip, so nothing jumps when the buttons appear. */}
            <div className={shown ? "" : "invisible"}>
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {GRADES.map((g) => (
                  <button
                    key={g.grade}
                    type="button"
                    disabled={busy}
                    onClick={() => grade(card, g.grade)}
                    className="flex min-h-16 flex-col items-center justify-center gap-0.5 rounded-md border border-rule-strong bg-raised px-2 py-2 hover:bg-sunk disabled:opacity-50"
                  >
                    <span className={`flex items-center gap-1.5 font-semibold ${g.tone}`}>
                      <Kbd className="hidden md:inline-flex">{g.key}</Kbd>
                      {g.label}
                    </span>
                    <span className="font-mono text-mono text-ink-2">{days(sm2(card.ef, card.interval, card.reps, g.grade)[1])}</span>
                  </button>
                ))}
              </div>
              <p className="mt-2 text-small text-ink-3">
                {card.reps === 0
                  ? "New cards come back tomorrow, whichever you pick; the gap grows after that."
                  : "Your grade also changes how fast the gap grows at later reviews."}
              </p>
            </div>
          </>
        )}
      </div>

      {DEMO && <p className="mt-6 text-small text-ink-3">Your cards are saved in this browser only.</p>}

      {slide && <SlideDialog slides={[slide]} index={0} onIndex={() => {}} onClose={() => setSlide(null)} />}
    </div>
  );
}

function CardTag({ card }: { card: Card }) {
  return (
    <p className="flex flex-wrap items-center gap-2">
      <Badge>{card.unit ?? "Card"}</Badge>
      <span className="text-small text-ink-3">{card.origin === "quiz" ? "from a quiz" : "generated"}</span>
    </p>
  );
}
