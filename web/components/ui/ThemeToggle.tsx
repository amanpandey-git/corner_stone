"use client";

import { Moon, Sun } from "lucide-react";

/** Both icons are rendered and CSS shows the right one, so the server and the browser always agree. */
export default function ThemeToggle() {
  function toggle() {
    const dark = document.documentElement.classList.toggle("dark");
    try {
      localStorage.setItem("theme", dark ? "dark" : "light");
    } catch {
      /* blocked storage: the choice lasts until the page is closed */
    }
  }
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Switch between light and dark theme"
      className="inline-flex h-11 w-11 items-center justify-center rounded-sm text-ink-2 hover:bg-sunk hover:text-ink"
    >
      <Sun size={20} strokeWidth={1.5} aria-hidden className="hidden dark:block" />
      <Moon size={20} strokeWidth={1.5} aria-hidden className="dark:hidden" />
    </button>
  );
}
