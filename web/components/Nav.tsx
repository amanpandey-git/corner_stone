"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getJSON, type Health } from "@/lib/api";

const PAGES = [
  { href: "/documents", label: "Documents" },
  { href: "/ask", label: "Ask" },
  { href: "/quiz", label: "Quiz" },
  { href: "/review", label: "Flashcards" },
];

/** Top bar: page links + API status (GET /health every 15 s). */
export default function Nav() {
  const path = usePathname();
  const [health, setHealth] = useState<Health | null | "down">(null);

  useEffect(() => {
    const check = () => getJSON<Health>("/health").then(setHealth, () => setHealth("down"));
    check();
    const t = setInterval(check, 15000);
    return () => clearInterval(t);
  }, []);

  const status =
    health === null ? ["bg-slate-300", "checking API"]
    : health === "down" ? ["bg-red-500", "API down"]
    : [health.llm_key_present ? "bg-green-500" : "bg-amber-500",
       `${health.documents} docs · ${health.chunks} chunks${health.llm_key_present ? "" : " · no LLM key"}`];

  return (
    <header className="border-b bg-white">
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-1 px-4 py-3">
        <Link href="/" className="mr-4 font-bold">Cornerstone</Link>
        {PAGES.map((p) => (
          <Link
            key={p.href}
            href={p.href}
            className={`rounded px-3 py-1 text-sm ${path.startsWith(p.href) ? "bg-slate-900 text-white" : "hover:bg-slate-100"}`}
          >
            {p.label}
          </Link>
        ))}
        <span className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          <span className={`inline-block h-2 w-2 rounded-full ${status[0]}`} />
          {status[1]}
        </span>
      </nav>
    </header>
  );
}
