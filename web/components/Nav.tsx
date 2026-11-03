"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ButtonLink } from "@/components/ui/Button";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { REPO_URL } from "@/lib/links";

const PAGES = [
  { href: "/ask", label: "Ask" },
  { href: "/quiz", label: "Quiz" },
  { href: "/review", label: "Flashcards" },
  { href: "/documents", label: "Documents" },
];

/** Quiet top bar. On phones the page links move to the bottom tab bar (TabBar.tsx). */
export default function Nav() {
  const path = usePathname();
  return (
    <header className="border-b">
      <nav aria-label="Main" className="page flex h-16 items-center gap-2">
        <Link href="/" className="inline-flex min-h-11 items-center font-display text-[1.375rem] font-semibold tracking-tight">
          <span className="hl mr-px">S</span>ynapse
        </Link>
        <div className="ml-6 hidden items-center gap-1 md:flex">
          {PAGES.map((p) => {
            const on = path.startsWith(p.href);
            return (
              <Link
                key={p.href}
                href={p.href}
                aria-current={on ? "page" : undefined}
                className={`inline-flex min-h-11 items-center rounded-sm px-3 text-small ${on ? "bg-marker font-semibold text-on-marker" : "text-ink-2 hover:bg-sunk hover:text-ink"}`}
              >
                {p.label}
              </Link>
            );
          })}
        </div>
        <div className="ml-auto flex items-center gap-1">
          <a href={REPO_URL} rel="noreferrer" className="hidden min-h-11 items-center rounded-sm px-3 text-small text-ink-2 hover:bg-sunk hover:text-ink md:inline-flex">
            GitHub
          </a>
          <ThemeToggle />
          {path === "/" && (
            <ButtonLink href="/ask" variant="marker" size="sm" className="ml-1">
              Try the demo
            </ButtonLink>
          )}
        </div>
      </nav>
    </header>
  );
}
