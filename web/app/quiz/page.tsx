"use client";

import { ArrowRight, Check, RotateCcw, X } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import Notice from "@/components/Notice";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Kbd } from "@/components/ui/Kbd";
import { Skeleton } from "@/components/ui/Skeleton";
import { SlideDialog, SlideImage, type Slide } from "@/components/ui/SlidePanel";
import { getJSON, postJSON, type Card as FlashCard, type DocumentRow, type Quiz, type QuizQuestion } from "@/lib/api";
import { plural, splitLabel } from "@/lib/format";
import { friendlyError } from "@/lib/messages";

const SIZES = [5, 10];
const letter = (i: number) => String.fromCharCode(65 + i);
const toSlide = (q: QuizQuestion): Slide => ({ label: q.source.label, image_url: q.source.image_url, section: q.source.section });

type CardState = "idle" | "saving" | "created" | "exists" | "failed";

export default function QuizPage() {
  const [units, setUnits] = useState<string[]>([]);
  const [unit, setUnit] = useState("");
  const [n, setN] = useState(5);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [picks, setPicks] = useState<Record<number, number>>({});
  const [index, setIndex] = useState(0);
  const [finished, setFinished] = useState(false);
  const [cards, setCards] = useState<Record<number, CardState>>({});
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [slide, setSlide] = useState<Slide | null>(null);

  useEffect(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (docs) => setUnits([...new Set(docs.map((d) => d.unit).filter((u): u is string => !!u))].sort()),
      (e) => setError(e),
    );
  }, []);

  async function generate() {
    setBusy(true);
    setError(null);
    setQuiz(null);
    setPicks({});
    setIndex(0);
    setFinished(false);
    setCards({});
    try {
      // a new seed each time so "Generate" gives a different set of slides
      setQuiz(await postJSON<Quiz>("/quiz", { units: unit ? [unit] : undefined, n, seed: Date.now() % 100000 }));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  function retry() {
    // The same questions again: no model call, no quota.
    setPicks({});
    setIndex(0);
    setFinished(false);
  }

  const toFlashcard = useCallback(async (i: number, q: QuizQuestion) => {
    setCards((c) => ({ ...c, [i]: "saving" }));
    try {
      const r = await postJSON<{ card: FlashCard; created: boolean }>("/flashcards/from-quiz", q);
      setCards((c) => ({ ...c, [i]: r.created ? "created" : "exists" }));
    } catch {
      setCards((c) => ({ ...c, [i]: "failed" }));
    }
  }, []);

  const questions = quiz?.questions ?? [];
  const total = questions.length;
  const correct = questions.filter((q, i) => picks[i] === q.answer).length;

  return (
    <div className="page max-w-3xl pt-6 md:pt-10">
      <header className="ruled">
        <h1 className="text-h1">Quiz</h1>
        <p className="mt-1 text-ink-2">Questions written from your slides, each answer cited to its slide.</p>
      </header>

      {!quiz && !busy && (
        <Card className="mt-6 flex flex-wrap items-end gap-x-5 gap-y-4 p-4 md:p-5">
          <label className="flex flex-col gap-1 text-small text-ink-2">
            Unit
            <select value={unit} onChange={(e) => setUnit(e.target.value)} className="min-h-11 rounded-md border border-rule-strong bg-raised px-2 text-body text-ink">
              <option value="">All units</option>
              {units.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </label>
          <fieldset className="flex flex-col gap-1 text-small text-ink-2">
            <legend className="mb-1">Questions</legend>
            <div className="flex rounded-md bg-sunk p-0.5">
              {SIZES.map((s) => (
                <label key={s} className={`inline-flex min-h-10 min-w-12 items-center justify-center rounded-[8px] px-3 text-body has-focus-visible:outline-2 has-focus-visible:outline-ink ${n === s ? "bg-marker font-semibold text-on-marker" : "text-ink-2 hover:text-ink"}`}>
                  <input type="radio" name="size" value={s} checked={n === s} onChange={() => setN(s)} className="sr-only" />
                  {s}
                </label>
              ))}
            </div>
          </fieldset>
          <Button size="md" onClick={generate} className="ml-auto">Generate quiz</Button>
        </Card>
      )}

      {busy && (
        <div className="mt-6 space-y-3" role="status" aria-label="Writing your quiz">
          <p className="text-small text-ink-3">Writing your quiz from the slides...</p>
          <Skeleton className="h-8 w-4/5" />
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-14 w-full rounded-md" />)}
        </div>
      )}

      {error != null && <ErrorState className="mt-6" error={error} onRetry={generate} />}

      {quiz && total === 0 && (
        <div className="mt-6">
          <EmptyState title="No questions came back" action={<Button onClick={generate}>Try again</Button>}>
            None of the generated questions passed validation, so none are shown.
          </EmptyState>
        </div>
      )}

      {quiz && total > 0 && quiz.generated < quiz.requested && !finished && (
        <div className="mt-6">
          <Notice kind="warn">
            {quiz.generated} of {quiz.requested} questions passed validation ({quiz.rejected.length} rejected).
          </Notice>
        </div>
      )}

      {quiz && total > 0 && !finished && (
        <Question
          key={index}
          q={questions[index]}
          index={index}
          total={total}
          unit={unit}
          pick={picks[index]}
          card={cards[index] ?? "idle"}
          dialogOpen={!!slide}
          onPick={(o) => setPicks((p) => ({ ...p, [index]: o }))}
          onSource={() => setSlide(toSlide(questions[index]))}
          onFlashcard={() => toFlashcard(index, questions[index])}
          onNext={() => (index + 1 < total ? setIndex(index + 1) : setFinished(true))}
        />
      )}

      {quiz && total > 0 && finished && (
        <Score
          questions={questions}
          picks={picks}
          correct={correct}
          cards={cards}
          onRetry={retry}
          onNew={() => { setQuiz(null); setFinished(false); setPicks({}); setIndex(0); setCards({}); }}
          onSource={(q) => setSlide(toSlide(q))}
          onCardAll={() => questions.forEach((q, i) => {
            if (picks[i] !== q.answer && (cards[i] ?? "idle") === "idle") toFlashcard(i, q);
          })}
        />
      )}

      {slide && <SlideDialog slides={[slide]} index={0} onIndex={() => {}} onClose={() => setSlide(null)} />}
    </div>
  );
}

function CardStatus({ state }: { state: CardState }) {
  const text = { idle: "", saving: "Saving...", created: "Flashcard added.", exists: "Already a flashcard.", failed: friendlyError(new Error("flashcard")).text }[state];
  return <span role="status" className="text-small text-ink-2">{text}</span>;
}

function Question({ q, index, total, unit, pick, card, dialogOpen, onPick, onSource, onFlashcard, onNext }: {
  q: QuizQuestion;
  index: number;
  total: number;
  unit: string;
  pick: number | undefined;
  card: CardState;
  dialogOpen: boolean;
  onPick: (o: number) => void;
  onSource: () => void;
  onFlashcard: () => void;
  onNext: () => void;
}) {
  const done = pick !== undefined;
  const right = pick === q.answer;
  const next = useRef<HTMLButtonElement>(null);
  const { deck, page } = splitLabel(q.source.label);
  const answered = index + (done ? 1 : 0);

  useEffect(() => {
    if (done) next.current?.focus({ preventScroll: true });
  }, [done]);

  // A to D or 1 to 4 to answer, Enter for next. Never while typing or while a slide is open.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (dialogOpen || e.ctrlKey || e.metaKey || e.altKey) return;
      const tag = (e.target as HTMLElement).tagName;
      if (["INPUT", "SELECT", "TEXTAREA"].includes(tag)) return;
      if (!done) {
        const k = e.key.toLowerCase();
        const i = "abcd".indexOf(k) >= 0 ? "abcd".indexOf(k) : "1234".indexOf(k);
        if (k.length === 1 && i >= 0 && i < q.options.length) onPick(i);
      } else if (e.key === "Enter" && tag !== "BUTTON" && tag !== "A") {
        onNext();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [done, dialogOpen, q.options.length, onPick, onNext]);

  return (
    <section aria-label={`Question ${index + 1} of ${total}`} className="mt-6">
      <div className="flex items-baseline justify-between gap-4 text-small text-ink-2">
        <span>{unit || "All units"}</span>
        <span className="font-mono text-mono">Question {index + 1} of {total}</span>
      </div>
      <div role="progressbar" aria-label="Quiz progress" aria-valuemin={0} aria-valuemax={total} aria-valuenow={answered} className="mt-2 h-2 overflow-hidden rounded-full bg-sunk">
        <div className="h-full origin-left rounded-full bg-marker transition-transform duration-200" style={{ transform: `scaleX(${answered / total})` }} />
      </div>

      <h2 className="mt-6 text-h2">{q.question}</h2>

      <ul className="mt-5 space-y-2">
        {q.options.map((o, j) => {
          const isAnswer = done && j === q.answer;
          const isWrongPick = done && j === pick && !right;
          return (
            <li key={j}>
              <button
                type="button"
                disabled={done}
                onClick={() => onPick(j)}
                className={`flex min-h-14 w-full items-start gap-3 rounded-md border px-3 py-3 text-left disabled:cursor-default ${
                  isAnswer ? "border-correct bg-correct-bg text-correct"
                  : isWrongPick ? "border-wrong bg-wrong-bg text-wrong"
                  : done ? "bg-raised text-ink-2"
                  : "border-rule-strong bg-raised hover:bg-sunk"}`}
              >
                <Kbd className={isAnswer || isWrongPick ? "border-current text-current" : ""}>{letter(j)}</Kbd>
                <span className="flex-1">{o}</span>
                {isAnswer && <Check size={20} strokeWidth={2} aria-label="Correct answer" className="mt-0.5 shrink-0" />}
                {isWrongPick && <X size={20} strokeWidth={2} aria-label="Your answer, wrong" className="mt-0.5 shrink-0" />}
              </button>
            </li>
          );
        })}
      </ul>

      {!done && <p className="mt-3 hidden text-small text-ink-3 md:block">Press <Kbd>A</Kbd> to <Kbd>D</Kbd> to answer.</p>}

      {done && (
        <div className="mt-5 space-y-4">
          <div role="status" className="ruled">
            <p className={`flex items-center gap-1.5 font-semibold ${right ? "text-correct" : "text-wrong"}`}>
              {right ? <Check size={18} strokeWidth={2} aria-hidden /> : <X size={18} strokeWidth={2} aria-hidden />}
              {right ? "Correct." : `Wrong: the answer is ${letter(q.answer)}.`}
            </p>
            <p className="mt-1">{q.explanation}</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-[13rem_minmax(0,1fr)] sm:items-start">
            <button type="button" onClick={onSource} aria-label={`Open the source slide: ${q.source.label}`} className="block rounded-md text-left">
              <SlideImage slide={toSlide(q)} sizes="208px" />
            </button>
            <div className="space-y-3">
              <p className="text-small text-ink-2">
                Source: {deck}{page && <span className="font-mono text-mono"> · {page}</span>}
              </p>
              {!right && (card === "idle"
                ? <Button variant="secondary" size="sm" onClick={onFlashcard}>Make flashcard</Button>
                : <CardStatus state={card} />)}
            </div>
          </div>
          <div className="flex justify-end">
            <Button ref={next} onClick={onNext}>
              {index + 1 < total ? "Next question" : "See your score"}
              <ArrowRight size={18} strokeWidth={1.75} aria-hidden />
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

/** The score, marked on the paper in red pen. */
function Score({ questions, picks, correct, cards, onRetry, onNew, onSource, onCardAll }: {
  questions: QuizQuestion[];
  picks: Record<number, number>;
  correct: number;
  cards: Record<number, CardState>;
  onRetry: () => void;
  onNew: () => void;
  onSource: (q: QuizQuestion) => void;
  onCardAll: () => void;
}) {
  const total = questions.length;
  const wrong = total - correct;
  const carded = questions.filter((q, i) => picks[i] !== q.answer && ["created", "exists"].includes(cards[i] ?? "")).length;
  return (
    <section aria-labelledby="score" className="mt-8">
      <div className="flex flex-wrap items-center gap-6">
        <p id="score" className="-rotate-2 rounded-[50%] border-2 border-margin-pen px-7 py-3 font-display text-display lining-nums">
          {correct} / {total}
        </p>
        <p className="max-w-[28ch] text-lede text-ink-2">
          {correct === total ? "Full marks." : `${plural(wrong, "question")} to go back to.`}
        </p>
      </div>

      <ol className="mt-8 divide-y border-y">
        {questions.map((q, i) => {
          const right = picks[i] === q.answer;
          const { deck, page } = splitLabel(q.source.label);
          return (
            <li key={i} className="flex items-start gap-3 py-3">
              <Badge tone={right ? "correct" : "wrong"} className="mt-0.5">
                {right ? <Check size={14} strokeWidth={2} aria-label="Correct" /> : <X size={14} strokeWidth={2} aria-label="Wrong" />}
              </Badge>
              <div className="min-w-0 flex-1">
                <p>{q.question}</p>
                <button type="button" onClick={() => onSource(q)} className="-my-2 inline-flex min-h-11 items-center text-left text-small text-accent-ink underline-offset-4 hover:underline">
                  {deck}{page && <span className="ml-1 font-mono text-mono">· {page}</span>}
                </button>
              </div>
            </li>
          );
        })}
      </ol>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Button onClick={onRetry}>
          <RotateCcw size={18} strokeWidth={1.75} aria-hidden />
          Retry these questions
        </Button>
        <Button variant="secondary" onClick={onNew}>New quiz</Button>
      </div>
      {wrong > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-3">
          {carded < wrong
            ? <Button variant="ghost" size="sm" onClick={onCardAll}>Review wrong answers as flashcards</Button>
            : (
              <p role="status" className="text-small text-ink-2">
                Saved as flashcards.{" "}
                <Link href="/review" className="font-semibold underline decoration-rule-strong underline-offset-4 hover:decoration-ink">Open Flashcards</Link>
              </p>
            )}
        </div>
      )}
    </section>
  );
}
