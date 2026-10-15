"use client";

import { Fragment } from "react";

// The same marker shapes citations.py accepts: [1], [1, 2], [1-3]. Display only: the API has already
// parsed, validated and checked the citations; this just makes each number clickable.
const MARKER = /\[\s*\d+(?:\s*[,\-–]\s*\d+)*\s*\]/g;

function numbers(marker: string): number[] {
  const out: number[] = [];
  for (const part of marker.slice(1, -1).split(",")) {
    const [a, b] = part.split(/[-–]/).map((x) => parseInt(x.trim(), 10));
    if (b === undefined) out.push(a);
    else for (let i = a; i <= b; i++) out.push(i);
  }
  return out;
}

/** Answer text with every [n] turned into a button that opens source n. */
export default function CitedText({ text, onCite }: { text: string; onCite: (n: number) => void }) {
  const pieces: React.ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(MARKER)) {
    pieces.push(text.slice(last, m.index));
    pieces.push(
      <Fragment key={m.index}>
        {numbers(m[0]).map((n) => (
          <button
            key={n}
            onClick={() => onCite(n)}
            className="mx-0.5 rounded bg-blue-100 px-1 text-xs font-semibold text-blue-800 align-super hover:bg-blue-200"
            title={`Open source ${n}`}
          >
            {n}
          </button>
        ))}
      </Fragment>,
    );
    last = m.index + m[0].length;
  }
  pieces.push(text.slice(last));
  return <div className="whitespace-pre-wrap leading-relaxed">{pieces}</div>;
}
