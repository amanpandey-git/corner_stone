"use client";

import { CircleX, RotateCcw, TriangleAlert, WifiOff } from "lucide-react";
import { useMemo } from "react";
import { friendlyError } from "@/lib/messages";
import { Button } from "./Button";
import { cx } from "./cx";

/** Every failure on the page goes through here, so raw error text can never reach the user. */
export function ErrorState({ error, onRetry, className }: { error: unknown; onRetry?: () => void; className?: string }) {
  const f = useMemo(() => friendlyError(error), [error]);
  const calm = f.kind === "rate" || f.kind === "input";
  const Icon = f.kind === "connection" ? WifiOff : calm ? TriangleAlert : CircleX;
  return (
    <div role="alert" className={cx("flex flex-wrap items-start gap-3 rounded-md p-4", calm ? "bg-warn-bg text-warn" : "bg-wrong-bg text-wrong", className)}>
      <Icon size={20} strokeWidth={1.5} aria-hidden className="mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{f.title}</p>
        <p className="text-small">{f.text}</p>
      </div>
      {f.retry && onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RotateCcw size={16} strokeWidth={1.5} aria-hidden />
          Try again
        </Button>
      )}
    </div>
  );
}
