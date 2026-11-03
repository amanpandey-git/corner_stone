import { ArrowRight, Check } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import HeroAnswer from "@/components/HeroAnswer";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SlideImage } from "@/components/ui/SlidePanel";
import { Tally } from "@/components/ui/Stat";
import { deckName, splitLabel } from "@/lib/format";
import { REPO_URL, REPORT_URL } from "@/lib/links";
import { RECORDED_ANSWER, RECORDED_QUIZ, RECORDED_REFUSAL } from "@/lib/recorded";

// How it works, set as a textbook's contents page. Numbers: docs/evaluation-report.md and PROGRESS.md.
const CONTENTS = [
  { name: "Upload", href: "/documents", value: "7 decks, 422 slide pages", note: "In the full app. This demo comes with the decks already indexed." },
  { name: "Index", href: "/documents", value: "328 chunks, 24 copied slides skipped", note: "Every page is indexed, or flagged with a reason." },
  { name: "Ask", href: "/ask", value: "claims cited to their slides", note: "Anything uncited is flagged. If the notes do not cover it, it says “Not in your notes.”" },
  { name: "Revise", href: "/quiz", value: "quiz, then spaced flashcards", note: "A wrong quiz answer can become a flashcard." },
];

// The marksheet. Every number is copied from docs/evaluation-report.md or PROGRESS.md; nothing is rounded up.
const MARKS: { meaning: string; metric: string; result: string; tally?: [number, number]; fraction?: string }[] = [
  { meaning: "Finds the right slide in its top 5", metric: "hit@5", result: "0.939", fraction: "31/33", tally: [31, 33] },
  { meaning: "Ranks the right slide near the top", metric: "MRR", result: "0.856" },
  { meaning: "A cited slide really says it (LLM-judged)", metric: "Citation accuracy", result: "100%", fraction: "75/75", tally: [75, 75] },
  { meaning: "The whole answer sticks to the slides (LLM-judged)", metric: "Faithfulness", result: "96.9%", fraction: "31/32", tally: [31, 32] },
  { meaning: "Refuses questions the notes do not cover", metric: "Correct refusals", result: "10/10", tally: [10, 10] },
  { meaning: "First words appear (median)", metric: "First token p50", result: "884 ms" },
  { meaning: "Search time (95th percentile)", metric: "Search p95", result: "47 ms" },
  { meaning: "Generated quiz questions that pass validation", metric: "Quiz validity", result: "25/25", tally: [25, 25] },
  { meaning: "Automated tests passing", metric: "Tests", result: "274" },
];

const MODES = [
  { name: "2 marks", size: "40-60 words" },
  { name: "5 marks", size: "150-250 words" },
  { name: "10 marks", size: "400-600 words" },
];

const FLOW = [
  { title: "Your question", text: "Asked in any of the five answer modes." },
  { title: "Search in your browser", text: "The embedding model, quantised for the browser, finds the closest slides among 328 chunks." },
  { title: "Top 5 slides", text: "The browser sends only their ids; the server builds the prompt from its own copy." },
  { title: "Groq writes", text: "Told to answer only from those slides, or to say they do not answer it." },
  { title: "Cited answer", text: "Streams back, each citation tied to its slide." },
];

function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="mb-2 font-mono text-mono tracking-wide text-ink-3 uppercase">{children}</p>;
}

function Tile({ title, className, children }: { title: string; className?: string; children: ReactNode }) {
  return (
    <Card className={`flex flex-col gap-4 p-5 md:p-6 ${className ?? ""}`}>
      <h3 className="text-h3">{title}</h3>
      {children}
    </Card>
  );
}

export default function Home() {
  const cited = RECORDED_ANSWER.sources.find((s) => s.n === 1)!;
  const retrieved = [...RECORDED_ANSWER.sources];
  return (
    <>
      {/* Hero */}
      <section className="page grid items-start gap-10 pt-10 pb-16 md:pt-16 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:gap-14 lg:pb-24">
        <div className="ruled lg:py-6">
          <h1 className="text-display">
            Ask your lecture slides. Get answers with <span className="hl">the slide they came from.</span>
          </h1>
          <p className="mt-6 max-w-[34rem] text-lede text-ink-2">
            An exam-prep assistant that answers only from your notes, and says so when it can&rsquo;t.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-x-4 gap-y-3">
            <ButtonLink href="/ask" variant="marker" size="lg">
              Try the demo
              <ArrowRight size={18} strokeWidth={1.75} aria-hidden />
            </ButtonLink>
            <a href="#results" className="inline-flex min-h-11 items-center px-1 font-semibold underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
              See the results
            </a>
          </div>
        </div>
        <HeroAnswer />
      </section>

      {/* How it works: a contents page, not a strip of step cards */}
      <section aria-labelledby="how" className="page reveal py-12 md:py-20">
        <div className="ruled">
          <Eyebrow>Contents</Eyebrow>
          <h2 id="how" className="text-h2">How it works</h2>
          <ol className="mt-8 max-w-4xl divide-y">
            {CONTENTS.map((c, i) => (
              <li key={c.name} className="py-4">
                <Link href={c.href} className="group block rounded-sm">
                  <span className="flex items-baseline">
                    <span className="w-6 shrink-0 font-mono text-mono text-ink-3">{i + 1}</span>
                    <span className="font-display text-h3 font-semibold group-hover:underline group-hover:underline-offset-4">{c.name}</span>
                    <span aria-hidden className="leader" />
                    <span className="min-w-0 text-right text-small font-semibold md:text-body">{c.value}</span>
                  </span>
                  <span className="mt-1 block pl-6 text-small text-ink-3">{c.note}</span>
                </Link>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Features: unequal tiles, each showing real output from this demo */}
      <section aria-labelledby="features" className="page py-12 md:py-20">
        <Eyebrow>What it does</Eyebrow>
        <h2 id="features" className="text-h2">Real output, not promises</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-12">
          <Tile title="Cited answers" className="reveal md:col-span-2 lg:col-span-7">
            <div className="grid gap-5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
              <div className="space-y-3">
                <p className="text-ink-2">Claims carry their source, and the source is the actual slide with its page number. Anything uncited is flagged.</p>
                <p className="leading-relaxed">
                  It is easy to implement<span aria-label="Source 1" className="mx-0.5 inline-flex h-[1.15rem] min-w-[1.15rem] -translate-y-[0.3em] items-center justify-center rounded-[4px] bg-marker px-1 font-mono text-[0.6875rem] leading-none font-semibold text-on-marker">1</span>. Requests do not have to wait in a queue<span aria-label="Source 1" className="mx-0.5 inline-flex h-[1.15rem] min-w-[1.15rem] -translate-y-[0.3em] items-center justify-center rounded-[4px] bg-marker px-1 font-mono text-[0.6875rem] leading-none font-semibold text-on-marker">1</span>.
                </p>
              </div>
              <div className="space-y-1.5">
                <SlideImage slide={cited} sizes="(min-width: 1024px) 340px, 100vw" />
                <p className="font-mono text-mono text-ink-3">{splitLabel(cited.label).page}</p>
              </div>
            </div>
          </Tile>

          <Tile title="Honest refusals" className="reveal md:col-span-1 lg:col-span-5">
            <p className="rounded-md bg-sunk px-3 py-2 text-small font-semibold">{RECORDED_REFUSAL.question}</p>
            <p className="font-display text-h1 font-semibold">{RECORDED_REFUSAL.text}</p>
            <p className="mt-auto text-small text-ink-2">
              Networking is not in these operating-systems slides, so Synapse says so instead of guessing.
            </p>
          </Tile>

          <Tile title="Exam modes" className="reveal md:col-span-1 lg:col-span-4">
            <p className="text-small text-ink-2">Answers shaped like university marks, still cited.</p>
            <ul className="mt-auto divide-y">
              {MODES.map((m) => (
                <li key={m.name} className="flex items-baseline justify-between py-2">
                  <span className="font-display text-h3 font-semibold">{m.name}</span>
                  <span className="font-mono text-mono text-ink-3">{m.size}</span>
                </li>
              ))}
            </ul>
          </Tile>

          <Tile title="Quiz generator" className="reveal md:col-span-1 lg:col-span-4">
            <p className="text-small font-semibold">{RECORDED_QUIZ.question}</p>
            <ul className="space-y-1.5 text-small">
              {RECORDED_QUIZ.options.slice(0, 2).map((o, i) => (
                <li key={o} className={`flex gap-2 rounded-sm px-2 py-1.5 ${i === RECORDED_QUIZ.answer ? "bg-correct-bg text-correct" : "bg-sunk text-ink-2"}`}>
                  <span className="font-mono text-mono">{String.fromCharCode(65 + i)}</span>
                  <span className="flex-1">{o}</span>
                  {i === RECORDED_QUIZ.answer && <Check size={16} strokeWidth={2} aria-label="Correct answer" className="mt-0.5 shrink-0" />}
                </li>
              ))}
            </ul>
            <p className="mt-auto font-mono text-mono text-ink-3">{deckName(splitLabel(RECORDED_QUIZ.label).deck)} · {splitLabel(RECORDED_QUIZ.label).page}</p>
          </Tile>

          <Tile title="SM-2 flashcards" className="reveal md:col-span-1 lg:col-span-4">
            <div className="rounded-md border p-3">
              <p className="text-small font-semibold">{RECORDED_QUIZ.question}</p>
              <p className="mt-2 border-t pt-2 text-small text-ink-2">{RECORDED_QUIZ.options[RECORDED_QUIZ.answer]}.</p>
            </div>
            <p className="mt-auto text-small text-ink-2">
              This card was made from a wrong quiz answer. SM-2 spaced repetition then decides when you see it again.
            </p>
          </Tile>

          <Tile title="Semantic search" className="reveal md:col-span-2 lg:col-span-12">
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
              <p className="text-small text-ink-2">
                It searches by meaning, not by matching words, and it runs in your browser. These are the {retrieved.length} slides it found for the question above.
              </p>
              <ol className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
                {retrieved.map((s) => (
                  <li key={s.n} className="flex items-baseline gap-2 text-small">
                    <span className="font-mono text-mono text-ink-3">{splitLabel(s.label).page}</span>
                    <span>{s.section}</span>
                  </li>
                ))}
              </ol>
            </div>
          </Tile>
        </div>
      </section>

      {/* Results: a marksheet, not a stats band */}
      <section id="results" aria-labelledby="marks" className="page scroll-mt-6 py-12 md:py-20">
        <div className="ruled">
          <Eyebrow>Marksheet</Eyebrow>
          <h2 id="marks" className="text-h2">Results, with the working shown</h2>
          <p className="mt-3 max-w-[60ch] text-ink-2">
            Answer metrics are for <strong className="font-bold text-ink">concise mode</strong> on the test split: 7 decks, 33 answerable and 10 unanswerable questions.
          </p>
          <ul className="mt-8 border-t">
            {MARKS.map((m) => (
              <li key={m.metric} className="reveal grid gap-x-6 gap-y-1 border-b py-3 md:grid-cols-[minmax(0,1.5fr)_minmax(0,0.9fr)_minmax(0,0.8fr)_minmax(0,1.5fr)] md:items-center">
                <span>{m.meaning}</span>
                <span className="font-mono text-mono text-ink-3">{m.metric}</span>
                <span className="font-display text-h3 font-semibold lining-nums tabular-nums">
                  {m.result}
                  {m.fraction && <span className="ml-2 font-mono text-mono font-medium text-ink-3">{m.fraction}</span>}
                </span>
                {m.tally ? <Tally hit={m.tally[0]} total={m.tally[1]} /> : <span aria-hidden className="hidden md:block" />}
              </li>
            ))}
          </ul>
          <p className="mt-6 max-w-[60ch] text-ink-2">
            Measured on the full system on a laptop. These numbers were not re-measured on this online demo.
          </p>
          <a href={REPORT_URL} rel="noreferrer" className="mt-4 inline-flex min-h-11 items-center gap-2 font-semibold underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
            Read the evaluation report, including where it falls short
            <ArrowRight size={18} strokeWidth={1.75} aria-hidden />
          </a>
        </div>
      </section>

      {/* Under the hood */}
      <section aria-labelledby="hood" className="page reveal py-12 md:py-20">
        <Eyebrow>Under the hood</Eyebrow>
        <h2 id="hood" className="text-h2">The path of one question</h2>
        <ol className="mt-8 grid gap-6 border-t pt-6 md:grid-cols-5 md:gap-5">
          {FLOW.map((f, i) => (
            <li key={f.title}>
              <p className="font-mono text-mono text-ink-3">{i + 1}</p>
              <p className="mt-1 font-bold">{f.title}</p>
              <p className="mt-1 text-small text-ink-2">{f.text}</p>
            </li>
          ))}
        </ol>
        <dl className="mt-8 grid gap-3 text-small md:grid-cols-[auto_minmax(0,1fr)] md:gap-x-6">
          <dt className="font-mono text-mono text-ink-3">This demo</dt>
          <dd>Next.js, React, Tailwind CSS, transformers.js with bge-small-en-v1.5, Groq with gpt-oss-120b</dd>
          <dt className="font-mono text-mono text-ink-3">Full app</dt>
          <dd>Python, FastAPI, FAISS HNSW, SQLite, plus uploads and a saved flashcard store</dd>
        </dl>
      </section>

      {/* A project title page, not a developer card */}
      <section aria-labelledby="project" className="page reveal py-12 md:py-20">
        <div className="mx-auto max-w-2xl border-y-4 border-double border-rule-strong px-4 py-12 text-center md:py-16">
          <h2 id="project" className="font-display text-h1">Synapse</h2>
          <p className="mx-auto mt-3 max-w-[32rem] text-ink-2">An exam-prep assistant for students studying their own course slides.</p>
          <p className="mt-8 text-small text-ink-3">Submitted by</p>
          <p className="font-display text-h3 font-semibold">Aman Pandey</p>
          <p className="text-small text-ink-2">B.Tech CSE, MITS Gwalior</p>
          <p className="mt-6 text-small text-ink-3">Under the guidance of</p>
          <p className="font-display text-h3 font-semibold">Dr. Manish Dixit</p>
          <a href={REPO_URL} rel="noreferrer" className="mt-8 inline-flex min-h-11 items-center gap-2 font-semibold underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
            Source code on GitHub
            <ArrowRight size={18} strokeWidth={1.75} aria-hidden />
          </a>
        </div>
      </section>
    </>
  );
}
