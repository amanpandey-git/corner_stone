import Link from "next/link";

const STEPS = [
  { href: "/documents", title: "1. Upload your notes", text: "PDF or DOCX slides; each page is indexed or flagged with a reason." },
  { href: "/ask", title: "2. Ask", text: "Exam-style answers (2, 5 or 10 marks) cited to the slide, or \"Not in your notes.\"" },
  { href: "/quiz", title: "3. Quiz", text: "MCQs from a unit, each answer cited to its slide." },
  { href: "/review", title: "4. Flashcards", text: "Spaced repetition (SM-2); wrong quiz answers become cards." },
];

export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Study from your own slides</h1>
      <div className="grid gap-4 sm:grid-cols-2">
        {STEPS.map((s) => (
          <Link key={s.href} href={s.href} className="rounded-lg border bg-white p-4 hover:border-slate-400">
            <p className="font-semibold">{s.title}</p>
            <p className="text-sm text-slate-600">{s.text}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
