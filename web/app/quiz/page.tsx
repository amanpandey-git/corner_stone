"use client";

import { useEffect, useState } from "react";
import Notice from "@/components/Notice";
import SlideModal, { type Slide } from "@/components/SlideModal";
import { errorText, getJSON, postJSON, type Card, type DocumentRow, type Quiz, type QuizQuestion } from "@/lib/api";

export default function QuizPage() {
  const [units, setUnits] = useState<string[]>([]);
  const [unit, setUnit] = useState("");
  const [n, setN] = useState(5);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [picks, setPicks] = useState<Record<number, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [slide, setSlide] = useState<Slide | null>(null);

  useEffect(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (docs) => setUnits([...new Set(docs.map((d) => d.unit).filter((u): u is string => !!u))].sort()),
      (e) => setError(errorText(e)),
    );
  }, []);

  async function generate() {
    setBusy(true);
    setError(null);
    setQuiz(null);
    setPicks({});
    try {
      // a new seed each time so "Generate" gives a different set of slides
      setQuiz(await postJSON<Quiz>("/quiz", { units: unit ? [unit] : undefined, n, seed: Date.now() % 100000 }));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  const answered = Object.keys(picks).length;
  const correct = quiz ? quiz.questions.filter((q, i) => picks[i] === q.answer).length : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Quiz</h1>
      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-white p-4 text-sm">
        <label className="flex items-center gap-2">
          Unit
          <select value={unit} onChange={(e) => setUnit(e.target.value)} className="rounded border px-2 py-1">
            <option value="">all</option>
            {units.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2">
          Questions
          <input type="number" min={1} max={10} value={n} onChange={(e) => setN(Number(e.target.value))} className="w-16 rounded border px-2 py-1" />
        </label>
        <button onClick={generate} disabled={busy || n < 1} className="ml-auto rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-40">
          {busy ? "Generating..." : "Generate quiz"}
        </button>
      </div>

      {error && <Notice>{error}</Notice>}

      {quiz && (
        <>
          {quiz.generated < quiz.requested && (
            <Notice kind="warn">
              {quiz.generated} of {quiz.requested} questions passed validation ({quiz.rejected.length} rejected).
            </Notice>
          )}
          <ol className="space-y-4">
            {quiz.questions.map((q, i) => (
              <QuestionCard
                key={i}
                q={q}
                index={i}
                pick={picks[i]}
                onPick={(o) => setPicks((p) => ({ ...p, [i]: o }))}
                onSource={() => setSlide({ label: q.source.label, image_url: q.source.image_url, section: q.source.section })}
              />
            ))}
          </ol>
          {answered === quiz.questions.length && quiz.questions.length > 0 && (
            <Notice kind="info">Score: {correct} / {quiz.questions.length}</Notice>
          )}
        </>
      )}
      <SlideModal slide={slide} onClose={() => setSlide(null)} />
    </div>
  );
}

function QuestionCard({ q, index, pick, onPick, onSource }: {
  q: QuizQuestion; index: number; pick: number | undefined; onPick: (o: number) => void; onSource: () => void;
}) {
  const [card, setCard] = useState<"idle" | "saving" | "created" | "exists" | string>("idle");
  const done = pick !== undefined;

  async function toFlashcard() {
    setCard("saving");
    try {
      const r = await postJSON<{ card: Card; created: boolean }>("/flashcards/from-quiz", q);
      setCard(r.created ? "created" : "exists");
    } catch (e) {
      setCard(errorText(e));
    }
  }

  return (
    <li className="space-y-2 rounded-lg border bg-white p-4">
      <p className="font-medium">{index + 1}. {q.question}</p>
      <div className="grid gap-2">
        {q.options.map((o, j) => {
          const style = !done ? "hover:bg-slate-100"
            : j === q.answer ? "border-green-500 bg-green-50"
            : j === pick ? "border-red-500 bg-red-50" : "opacity-60";
          return (
            <button key={j} disabled={done} onClick={() => onPick(j)} className={`rounded border px-3 py-2 text-left text-sm ${style}`}>
              {String.fromCharCode(65 + j)}. {o}
            </button>
          );
        })}
      </div>
      {done && (
        <div className="space-y-2 text-sm">
          <p className={pick === q.answer ? "text-green-700" : "text-red-700"}>
            {pick === q.answer ? "Correct." : `Wrong: the answer is ${String.fromCharCode(65 + q.answer)}.`} {q.explanation}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <button onClick={onSource} className="text-blue-700 hover:underline">Source: {q.source.label}</button>
            {pick !== q.answer && (
              card === "idle" ? (
                <button onClick={toFlashcard} className="rounded border px-2 py-1 hover:bg-slate-100">Make flashcard</button>
              ) : (
                <span className="text-slate-600">
                  {card === "saving" ? "Saving..." : card === "created" ? "Flashcard added." : card === "exists" ? "Already a flashcard." : card}
                </span>
              )
            )}
          </div>
        </div>
      )}
    </li>
  );
}
