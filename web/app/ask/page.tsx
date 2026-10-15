"use client";

import { useEffect, useRef, useState } from "react";
import CitedText from "@/components/CitedText";
import Notice from "@/components/Notice";
import SlideModal, { type Slide } from "@/components/SlideModal";
import { errorText, getJSON, MODES, streamAsk, type Answer, type DocumentRow, type Mode, type Source } from "@/lib/api";

const WHY: Record<string, string> = {
  retrieval: "nothing in your notes is close to this question",
  model: "the closest slides do not answer it",
  no_citations: "the model's answer could not be tied to any slide",
};

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<Mode>("concise");
  const [unit, setUnit] = useState("");
  const [check, setCheck] = useState(false);
  const [units, setUnits] = useState<string[]>([]);
  const [streamed, setStreamed] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [slide, setSlide] = useState<Slide | null>(null);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (docs) => setUnits([...new Set(docs.map((d) => d.unit).filter((u): u is string => !!u))].sort()),
      (e) => setError(errorText(e)),
    );
    return () => abort.current?.abort();
  }, []);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    setBusy(true);
    setError(null);
    setAnswer(null);
    setStreamed("");
    try {
      const final = await streamAsk(
        { question, mode, units: unit ? [unit] : undefined, check },
        (piece) => setStreamed((s) => s + piece),
        ctrl.signal,
      );
      setAnswer(final);
    } catch (err) {
      if (!ctrl.signal.aborted) setError(errorText(err));
    } finally {
      if (abort.current === ctrl) setBusy(false);
    }
  }

  const open = (s: Source | undefined) => s && setSlide({ label: s.label, image_url: s.image_url, section: s.section });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Ask your notes</h1>

      <form onSubmit={ask} className="space-y-3 rounded-lg border bg-white p-4">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), e.currentTarget.form?.requestSubmit())}
          rows={3}
          placeholder="e.g. Explain the access matrix model of protection."
          className="w-full rounded border p-2"
        />
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2">
            Answer as
            <select value={mode} onChange={(e) => setMode(e.target.value as Mode)} className="rounded border px-2 py-1">
              {MODES.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          <label className="flex items-center gap-2">
            Unit
            <select value={unit} onChange={(e) => setUnit(e.target.value)} className="rounded border px-2 py-1">
              <option value="">all</option>
              {units.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </label>
          <label className="flex items-center gap-2" title="A second model checks each cited sentence against its slide (slower, uses more LLM quota)">
            <input type="checkbox" checked={check} onChange={(e) => setCheck(e.target.checked)} />
            Check citations
          </label>
          <button
            type="submit"
            disabled={!question.trim() || busy}
            className="ml-auto rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-40"
          >
            {busy ? "Answering..." : "Ask"}
          </button>
        </div>
      </form>

      {error && <Notice>{error}</Notice>}

      {busy && !answer && (
        <div className="rounded-lg border bg-white p-4">
          {streamed ? <p className="whitespace-pre-wrap leading-relaxed">{streamed}</p>
                    : <p className="text-slate-500">Searching your notes...</p>}
        </div>
      )}

      {answer && <AnswerView answer={answer} check={check} onCite={(n) => open(answer.sources.find((s) => s.n === n))} onSource={open} />}

      <SlideModal slide={slide} onClose={() => setSlide(null)} />
    </div>
  );
}

function AnswerView({ answer, check, onCite, onSource }: {
  answer: Answer; check: boolean; onCite: (n: number) => void; onSource: (s: Source) => void;
}) {
  if (answer.abstained) {
    return (
      <Notice kind="info">
        <span className="font-semibold">{answer.text}</span> ({WHY[answer.abstain_reason ?? ""] ?? answer.abstain_reason})
      </Notice>
    );
  }
  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-white p-4">
        <CitedText text={answer.text} onCite={onCite} />
      </div>
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
      {check && answer.unsupported === null && <p className="text-xs text-slate-500">Citations could not be checked this time.</p>}

      <div>
        <h2 className="mb-2 font-semibold">Sources</h2>
        <ul className="space-y-2">
          {answer.sources.filter((s) => s.cited).map((s) => (
            <li key={s.n}>
              <button onClick={() => onSource(s)} className="w-full rounded border bg-white p-3 text-left hover:border-slate-400">
                <span className="mr-2 rounded bg-blue-100 px-1 text-xs font-semibold text-blue-800">{s.n}</span>
                <span className="font-medium">{s.label}</span>
                {s.section && <span className="text-slate-500"> · {s.section}</span>}
                <p className="mt-1 line-clamp-2 text-sm text-slate-600">{s.text}</p>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <p className="text-xs text-slate-500">
        {answer.provider} {answer.model} · first words after {Math.round(answer.ttft_ms ?? 0)} ms
        {answer.cached ? " · from cache" : ""}
      </p>
    </div>
  );
}
