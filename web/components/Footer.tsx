import Link from "next/link";
import HealthStatus from "@/components/HealthStatus";
import { REPO_URL, REPORT_URL } from "@/lib/links";

export default function Footer() {
  return (
    <footer className="mt-16 border-t">
      <div className="page flex flex-col gap-4 py-8 text-small text-ink-2 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <p>
            <span className="font-display text-[1.0625rem] font-semibold text-ink">Synapse</span>: answers only from your notes, with the slide to prove it.
          </p>
          <p>Aman Pandey, B.Tech CSE, MITS Gwalior. Guide: Dr. Manish Dixit.</p>
          <HealthStatus />
        </div>
        <ul className="flex flex-wrap gap-x-1">
          <li><Link href="/ask" className="inline-flex min-h-11 items-center rounded-sm px-2 underline-offset-4 hover:underline">Try the demo</Link></li>
          <li><a href={REPORT_URL} rel="noreferrer" className="inline-flex min-h-11 items-center rounded-sm px-2 underline-offset-4 hover:underline">Evaluation report</a></li>
          <li><a href={REPO_URL} rel="noreferrer" className="inline-flex min-h-11 items-center rounded-sm px-2 underline-offset-4 hover:underline">GitHub</a></li>
        </ul>
      </div>
    </footer>
  );
}
