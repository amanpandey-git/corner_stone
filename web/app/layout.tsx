import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import Footer from "@/components/Footer";
import Nav from "@/components/Nav";
import TabBar from "@/components/TabBar";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Synapse: ask your lecture slides", template: "%s · Synapse" },
  description: "Exam answers, quizzes and flashcards from your own notes, every claim cited to a slide.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FAF6EC" },
    { media: "(prefers-color-scheme: dark)", color: "#15130F" },
  ],
};

// Fonts are local files (OFL-1.1, licences beside them), so the app still builds and runs offline on demo day.
const fraunces = localFont({
  src: "./fonts/fraunces-latin-standard-normal.woff2",
  weight: "100 900",
  variable: "--font-fraunces",
  display: "swap",
  adjustFontFallback: "Times New Roman",
});
const atkinson = localFont({
  src: "./fonts/atkinson-hyperlegible-next-latin-wght-normal.woff2",
  weight: "200 800",
  variable: "--font-atkinson",
  display: "swap",
});
const jetbrains = localFont({
  src: "./fonts/jetbrains-mono-latin-wght-normal.woff2",
  weight: "100 800",
  variable: "--font-jetbrains",
  display: "swap",
  preload: false,
});

// Runs before first paint, so the page never flashes the wrong theme. Same key as the Tailwind docs: localStorage.theme.
const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem("theme");var d=t==="dark"||(!t&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.classList.toggle("dark",d)}catch(e){}})()`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning className={`${fraunces.variable} ${atkinson.variable} ${jetbrains.variable} h-full antialiased`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-marker focus:px-4 focus:py-2 focus:text-on-marker"
        >
          Skip to content
        </a>
        <Nav />
        <main id="main" tabIndex={-1} className="flex-1 focus:outline-none">{children}</main>
        <Footer />
        <TabBar />
      </body>
    </html>
  );
}
