"use client";

import { Fragment, useState, type CSSProperties, type ReactNode } from "react";
import { CitationChip } from "@/components/ui/CitationChip";

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

/** A claim, the chips that support it, and the punctuation that follows them. */
type Claim = { text: string; chips: number[]; tail: string };

const LEADING_PUNCT = /^[.,;:!?)\]]*\s*/;

function toClaims(line: string): Claim[] {
  const out: Claim[] = [];
  let cur: Claim = { text: "", chips: [], tail: "" };
  let last = 0;
  const between = (raw: string) => {
    if (!cur.chips.length) {
      cur.text += raw;
      return;
    }
    // After a chip: its full stop stays with it, so "requests [5]." never leaves a gap before the stop.
    const punct = raw.match(LEADING_PUNCT)?.[0] ?? "";
    const rest = raw.slice(punct.length);
    cur.tail += punct;
    if (rest) {
      out.push(cur);
      cur = { text: rest, chips: [], tail: "" };
    }
  };
  for (const m of line.matchAll(MARKER)) {
    between(line.slice(last, m.index));
    cur.text = cur.text.replace(/\s+$/, "");
    cur.chips.push(...numbers(m[0]));
    last = m.index + m[0].length;
  }
  between(line.slice(last));
  out.push(cur);
  return out;
}

type Block = { kind: "p" | "li" | "h"; text: string };

/** Long answers use a little Markdown: "- " bullets, "**bold**" and "### " headings. Display only; no words change. */
function toBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    const prev = blocks[blocks.length - 1];
    if (!line) {
      blocks.push({ kind: "p", text: "" });
    } else if (/^[-*•]\s+/.test(line)) {
      blocks.push({ kind: "li", text: line.replace(/^[-*•]\s+/, "") });
    } else if (/^#{1,6}\s+/.test(line)) {
      blocks.push({ kind: "h", text: line.replace(/^#{1,6}\s+/, "") });
    } else if (prev?.kind === "p" && prev.text) {
      prev.text += ` ${line}`;
    } else {
      blocks.push({ kind: "p", text: line });
    }
  }
  return blocks.filter((b) => b.text);
}

function bold(text: string): ReactNode {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.length === 1 ? text : parts.map((p, i) => (i % 2 ? <strong key={i} className="font-bold">{p}</strong> : p));
}

/**
 * Answer text with every [n] turned into a chip that opens source n. Focusing or hovering a chip sweeps highlighter
 * across the sentence it supports. `live` means the answer is still streaming, so chips show but cannot be clicked yet.
 * `stagger` makes the sentences arrive one by one, once (hero preview only).
 */
export default function CitedText({ text, onCite, labelFor, live, stagger }: {
  text: string;
  onCite?: (n: number) => void;
  labelFor?: (n: number) => string | undefined;
  live?: boolean;
  stagger?: boolean;
}) {
  const [on, setOn] = useState<string | null>(null);
  let order = 0;

  const claims = (id: string, line: string) =>
    toClaims(line).map((c, i) => {
      const key = `${id}.${i}`;
      const style = stagger ? ({ "--delay": `${200 + order++ * 260}ms` } as CSSProperties) : undefined;
      return (
        <span key={key} className={stagger ? "arrive" : undefined} style={style}>
          {c.chips.length ? <span className="sweep" data-on={on === key}>{bold(c.text)}</span> : bold(c.text)}
          {c.chips.map((n, j) => (
            <Fragment key={j}>
              <CitationChip
                n={n}
                label={labelFor?.(n)}
                disabled={live || !onCite}
                onOpen={() => onCite?.(n)}
                onActive={(active) => setOn(active ? key : null)}
              />
            </Fragment>
          ))}
          {c.tail}
        </span>
      );
    });

  const blocks = toBlocks(text);
  const out: ReactNode[] = [];
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i];
    if (b.kind === "li") {
      const items: ReactNode[] = [];
      let j = i;
      for (; j < blocks.length && blocks[j].kind === "li"; j++) {
        items.push(<li key={j} className="pl-1 marker:text-ink-3">{claims(`${j}`, blocks[j].text)}</li>);
      }
      out.push(<ul key={i} className="list-disc space-y-1.5 pl-5">{items}</ul>);
      i = j - 1;
    } else if (b.kind === "h") {
      out.push(<p key={i} className="font-bold">{claims(`${i}`, b.text)}</p>);
    } else {
      out.push(<p key={i}>{claims(`${i}`, b.text)}</p>);
    }
  }
  return <div className={`space-y-3 leading-relaxed ${live ? "caret" : ""}`}>{out}</div>;
}
