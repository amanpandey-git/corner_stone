"use client";

import { useState } from "react";
import CitedText from "@/components/CitedText";
import { Badge } from "@/components/ui/Badge";
import { SlideImage } from "@/components/ui/SlidePanel";
import { splitLabel } from "@/lib/format";
import { RECORDED_ANSWER as A } from "@/lib/recorded";

/**
 * The hero's preview: a real recorded answer with working citations. It swaps between the real slides and makes no
 * AI call, so it needs no model and no quota, and still works if the quota runs out during a demo.
 */
export default function HeroAnswer() {
  const [n, setN] = useState(5);
  const source = A.sources.find((s) => s.n === n) ?? A.sources[0];
  const { deck, page } = splitLabel(source.label);
  return (
    <figure className="rounded-xl border bg-raised p-4 shadow-sheet md:p-6">
      <figcaption className="mb-4 flex flex-wrap items-center justify-between gap-2 text-small text-ink-3">
        <span>Recorded from this demo</span>
        <Badge>{A.mode}</Badge>
      </figcaption>
      <p className="mb-4 rounded-md bg-sunk px-3 py-2 text-small font-semibold">{A.question}</p>
      <CitedText
        text={A.text}
        stagger
        onCite={setN}
        labelFor={(x) => A.sources.find((s) => s.n === x)?.label}
      />
      <div className="mt-5 space-y-2">
        <SlideImage slide={source} sizes="(min-width: 1024px) 480px, 100vw" />
        <p className="text-small text-ink-2">
          {deck}{page && <span className="font-mono text-mono"> · {page}</span>}
        </p>
        <p className="text-small text-ink-3">Press a yellow number to see the slide behind that sentence.</p>
      </div>
    </figure>
  );
}
