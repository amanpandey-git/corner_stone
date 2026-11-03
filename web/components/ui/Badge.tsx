import type { ComponentProps } from "react";
import { cx } from "./cx";

const TONES = {
  neutral: "border border-rule-strong text-ink-2",
  marker: "bg-marker text-on-marker",
  correct: "bg-correct-bg text-correct",
  wrong: "bg-wrong-bg text-wrong",
  warn: "bg-warn-bg text-warn",
};

/** A small mono label: marks, pages, counts. */
export function Badge({ tone = "neutral", className, ...rest }: ComponentProps<"span"> & { tone?: keyof typeof TONES }) {
  return <span className={cx("inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 font-mono text-mono", TONES[tone], className)} {...rest} />;
}
