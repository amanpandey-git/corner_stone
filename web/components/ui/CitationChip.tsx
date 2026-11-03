"use client";

/**
 * A numbered yellow tab at the end of a claim. Small on screen, but its invisible hit area is larger for fingers.
 * While an answer is still streaming the chip shows but cannot be clicked: the sources arrive with the final answer.
 */
export function CitationChip({ n, label, disabled, onOpen, onActive }: {
  n: number;
  label?: string;
  disabled?: boolean;
  onOpen?: () => void;
  onActive?: (active: boolean) => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onOpen}
      onMouseEnter={() => onActive?.(true)}
      onMouseLeave={() => onActive?.(false)}
      onFocus={() => onActive?.(true)}
      onBlur={() => onActive?.(false)}
      aria-label={label ? `Source ${n}: ${label}` : `Source ${n}`}
      title={label}
      className="relative mx-[0.08em] inline-flex h-[1.15rem] min-w-[1.15rem] -translate-y-[0.3em] items-center justify-center rounded-[4px] bg-marker px-1 align-baseline font-mono text-[0.6875rem] leading-none font-semibold text-on-marker after:absolute after:-inset-2.5 hover:brightness-95 disabled:cursor-default"
    >
      {n}
    </button>
  );
}
