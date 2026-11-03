import Link from "next/link";
import type { ComponentProps } from "react";
import { cx } from "./cx";

// Variant names follow shadcn/ui's convention (MIT); no code or dependency from it is used.
const BASE =
  "inline-flex items-center justify-center gap-2 rounded-md font-semibold whitespace-nowrap transition-[background-color,opacity,filter] duration-[120ms] disabled:cursor-not-allowed disabled:opacity-50";

const VARIANTS = {
  primary: "bg-ink text-paper hover:opacity-90",
  marker: "bg-marker text-on-marker hover:brightness-95",
  secondary: "border border-rule-strong bg-raised text-ink hover:bg-sunk",
  ghost: "text-ink-2 hover:bg-sunk hover:text-ink",
};

const SIZES = {
  sm: "min-h-11 px-3 text-small",
  md: "min-h-11 px-4 text-body",
  lg: "min-h-13 px-6 text-body",
};

type Style = { variant?: keyof typeof VARIANTS; size?: keyof typeof SIZES };

export function buttonClass({ variant = "primary", size = "md" }: Style = {}) {
  return cx(BASE, VARIANTS[variant], SIZES[size]);
}

export function Button({ variant, size, className, type = "button", ...rest }: ComponentProps<"button"> & Style) {
  return <button type={type} className={cx(buttonClass({ variant, size }), className)} {...rest} />;
}

export function ButtonLink({ variant, size, className, ...rest }: ComponentProps<typeof Link> & Style) {
  return <Link className={cx(buttonClass({ variant, size }), className)} {...rest} />;
}
