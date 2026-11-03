"use client";

import { FileText, GalleryVertical, ListChecks, MessageSquareText } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/ask", label: "Ask", Icon: MessageSquareText },
  { href: "/quiz", label: "Quiz", Icon: ListChecks },
  { href: "/review", label: "Flashcards", Icon: GalleryVertical },
  { href: "/documents", label: "Documents", Icon: FileText },
];

/** Phones only, app pages only: labelled tabs at thumb height, at least 56 px tall. */
export default function TabBar() {
  const path = usePathname();
  if (path === "/") return null;
  return (
    <>
      <div aria-hidden className="h-16 md:hidden" />
      <nav aria-label="App pages" className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t bg-raised pb-[env(safe-area-inset-bottom)] md:hidden">
        {TABS.map(({ href, label, Icon }) => {
          const on = path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={on ? "page" : undefined}
              className={`flex min-h-14 flex-col items-center justify-center gap-0.5 text-[0.75rem] leading-tight ${on ? "font-semibold text-ink" : "text-ink-2"}`}
            >
              <span className={`rounded-sm px-3 py-0.5 ${on ? "bg-marker text-on-marker" : ""}`}>
                <Icon size={20} strokeWidth={1.5} aria-hidden />
              </span>
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
