import type { ReactNode } from "react";

/** One measured number with what it means. The numbers come only from the evaluation report and PROGRESS.md. */
export function Stat({ value, label }: { value: ReactNode; label: ReactNode }) {
  return (
    <div>
      <p className="font-mono text-h3 tabular-nums">{value}</p>
      <p className="text-small text-ink-2">{label}</p>
    </div>
  );
}

/** A row of dots: `hit` filled out of `total`, so a score can be seen at a glance. Hidden from screen readers: the number is in the text. */
export function Tally({ hit, total }: { hit: number; total: number }) {
  return (
    <div aria-hidden className="tally">
      {Array.from({ length: total }, (_, i) => (
        <span key={i} data-miss={i >= hit} />
      ))}
    </div>
  );
}
