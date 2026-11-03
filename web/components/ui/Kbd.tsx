import type { ComponentProps } from "react";
import { cx } from "./cx";

/** A printed keyboard shortcut. */
export function Kbd({ className, ...rest }: ComponentProps<"kbd">) {
  return <kbd className={cx("inline-flex min-w-5 items-center justify-center rounded-sm border border-rule-strong px-1 font-mono text-[0.6875rem] leading-[1.15rem] font-medium text-ink-2", className)} {...rest} />;
}
