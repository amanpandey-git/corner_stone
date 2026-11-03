import type { ReactNode } from "react";
import { Card } from "./Card";

/** One sentence on what goes here, one action. */
export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <Card className="space-y-3 p-6 md:p-8">
      <h2 className="text-h2">{title}</h2>
      {children && <div className="max-w-[60ch] text-ink-2">{children}</div>}
      {action && <div className="flex flex-wrap items-center gap-3 pt-1">{action}</div>}
    </Card>
  );
}
