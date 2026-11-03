"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getJSON, type Health } from "@/lib/api";
import { plural } from "@/lib/format";

/**
 * A small status line in the footer. Checks GET /health once on load and when the tab regains focus (it used to poll
 * every 15 s for as long as a tab stayed open). Not shown on the landing page, which should load no demo code at all.
 */
export default function HealthStatus() {
  const path = usePathname();
  const active = path !== "/";
  const [health, setHealth] = useState<Health | "down" | null>(null);

  useEffect(() => {
    if (!active) return;
    const check = () => getJSON<Health>("/health").then(setHealth, () => setHealth("down"));
    check();
    window.addEventListener("focus", check);
    return () => window.removeEventListener("focus", check);
  }, [active]);

  if (!active) return null;
  // Holds the line open until the check returns, so the footer does not move.
  if (health === null) return <p aria-hidden className="h-[1.3125rem]" />;
  const [dot, text] =
    health === "down" ? ["bg-wrong", "Could not reach the service"]
    : health.llm_key_present ? ["bg-correct", `Online · ${plural(health.documents, "deck")} · ${health.chunks} chunks`]
    : ["bg-warn", `Search only: no AI key on this server · ${plural(health.documents, "deck")}`];
  return (
    <p className="flex items-center gap-2 text-ink-3" role="status">
      <span aria-hidden className={`inline-block h-2 w-2 rounded-full ${dot}`} />
      {text}
    </p>
  );
}
