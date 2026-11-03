"use client";

import { useCallback, useEffect, useState } from "react";
import Notice from "@/components/Notice";
import SlideModal, { type Slide } from "@/components/SlideModal";
import { errorText, getJSON, postJSON, type Card, type DocumentRow, type Due } from "@/lib/api";

// The same buttons as the Streamlit page; the SM-2 update itself runs in the API (srs.py).
const GRADES = [
  { label: "Again", grade: 1, style: "border-wrong hover:bg-wrong-bg" },
  { label: "Hard", grade: 3, style: "border-warn hover:bg-warn-bg" },
  { label: "Good", grade: 4, style: "border-correct hover:bg-correct-bg" },
  { label: "Easy", grade: 5, style: "border-rule-strong hover:bg-sunk" },
];

export default function ReviewPage() {
  const [units, setUnits] = useState<string[]>([]);
  const [unit, setUnit] = useState("");
  const [due, setDue] = useState<Due | null>(null);
  const [shown, setShown] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [slide, setSlide] = useState<Slide | null>(null);

  const load = useCallback(() => {
    const q = unit ? `&unit=${encodeURIComponent(unit)}` : "";
    getJSON<Due>(`/flashcards/due?limit=50${q}`).then(
      (d) => { setDue(d); setShown(false); },
      (e) => setError(errorText(e)),
    );
  }, [unit]);

  useEffect(load, [load]);
  useEffect(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (docs) => setUnits([...new Set(docs.map((d) => d.unit).filter((u): u is string => !!u))].sort()),
      (e) => setError(errorText(e)),
    );
  }, []);

  async function grade(card: Card, g: number) {
    setBusy(true);
    try {
      const next = await postJSON<Card>(`/flashcards/${card.card_id}/review`, { grade: g });
      setNote(`Next review of that card: ${next.due} (in ${next.interval} day${next.interval === 1 ? "" : "s"}).`);
      load();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const r = await postJSON<{ created: Card[]; skipped_duplicates: number; rejected: unknown[] }>(
        "/flashcards/generate", { units: unit ? [unit] : undefined, n: 10, seed: Date.now() % 100000 });
      setNote(`${r.created.length} cards created` + (r.skipped_duplicates ? `, ${r.skipped_duplicates} already existed` : "") + ".");
      load();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  const card = due?.cards[0];

  return (
    <div className="page space-y-6 py-8">
      <h1 className="text-2xl font-bold">Flashcards</h1>
      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-raised p-4 text-sm">
        <label className="flex items-center gap-2">
          Unit
          <select value={unit} onChange={(e) => setUnit(e.target.value)} className="rounded border px-2 py-1">
            <option value="">all</option>
            {units.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </label>
        {due && (
          <span className="text-ink-2">
            {due.cards.length} due now · {due.stats.cards} cards in total · {due.stats.reviews} reviews so far
          </span>
        )}
        <button onClick={generate} disabled={busy} className="ml-auto rounded border px-3 py-2 hover:bg-sunk disabled:opacity-40">
          {busy ? "Working..." : "Generate 10 cards"}
        </button>
      </div>

      {error && <Notice>{error}</Notice>}
      {note && <Notice kind="info">{note}</Notice>}

      {due && !card && (
        <Notice kind="info">
          No cards due{unit ? ` in ${unit}` : ""}. Generate cards above, or turn wrong quiz answers into cards.
        </Notice>
      )}

      {card && (
        <div className="space-y-4 rounded-lg border bg-raised p-6">
          <p className="text-xs uppercase text-ink-3">{card.unit ?? "card"} · {card.origin === "quiz" ? "from a quiz" : "generated"}</p>
          <p className="text-lg font-medium">{card.front}</p>
          {!shown ? (
            <button onClick={() => setShown(true)} className="rounded bg-ink px-4 py-2 text-sm text-paper">Show answer</button>
          ) : (
            <>
              <p className="whitespace-pre-wrap border-t pt-4">{card.back}</p>
              <button
                onClick={() => setSlide({ label: `${card.file_name}, p.${card.page ?? "?"}`, image_url: card.image_url ?? null })}
                className="text-sm text-accent-ink hover:underline"
              >
                Source: {card.file_name}{card.page != null ? `, p.${card.page}` : ""}
              </button>
              <div className="flex flex-wrap gap-2">
                {GRADES.map((g) => (
                  <button key={g.grade} disabled={busy} onClick={() => grade(card, g.grade)}
                          className={`rounded border-2 px-4 py-2 text-sm disabled:opacity-40 ${g.style}`}>
                    {g.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}
      <SlideModal slide={slide} onClose={() => setSlide(null)} />
    </div>
  );
}
