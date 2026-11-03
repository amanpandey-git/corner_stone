"use client";

import { ArrowRight, Trash2, Upload } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import Notice from "@/components/Notice";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { SlideImage } from "@/components/ui/SlidePanel";
import { DEMO, del, getJSON, uploadFiles, type DocumentRow, type Job } from "@/lib/api";
import { DEMO_OFF } from "@/lib/demo/core";
import { DECK_SEP, deckName, plural } from "@/lib/format";

const POLL_MS = 1000;

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentRow[] | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (d) => { setDocs(d); setError(null); },
      (e) => setError(e),
    );
  }, []);

  useEffect(refresh, [refresh]);

  // Poll every unfinished job; when one finishes, reload the document list.
  const pending = jobs.filter((j) => j.state === "queued" || j.state === "running").map((j) => j.job_id).join(",");
  useEffect(() => {
    if (!pending) return;
    const t = setInterval(async () => {
      const ids = pending.split(",");
      try {
        const fresh = await Promise.all(ids.map((id) => getJSON<Job>(`/documents/jobs/${id}`)));
        setJobs((old) => old.map((j) => fresh.find((f) => f.job_id === j.job_id) ?? j));
        if (fresh.some((f) => f.state === "done" || f.state === "failed")) refresh();
      } catch (e) {
        setError(e);
      }
    }, POLL_MS);
    return () => clearInterval(t);
  }, [pending, refresh]);

  async function upload() {
    setBusy(true);
    setError(null);
    try {
      const r = await uploadFiles(files);
      setJobs((old) => [...r.jobs.map((j) => ({ ...j, state: "queued" as const, report: null })), ...old]);
      setFiles([]);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  async function remove(d: DocumentRow) {
    if (!confirm(`Delete ${d.file_name}? Its slides will no longer be searched.`)) return;
    try {
      await del(`/documents/${d.doc_id}`);
      refresh();
    } catch (e) {
      setError(e);
    }
  }

  const pages = docs?.reduce((sum, d) => sum + d.pages_total, 0) ?? 0;
  const chunks = docs?.reduce((sum, d) => sum + d.chunks, 0) ?? 0;

  return (
    <div className="page pt-6 md:pt-10">
      <header className="ruled">
        <h1 className="text-h1">Documents</h1>
        <p className="mt-1 text-ink-2">
          {docs?.length
            ? <><strong className="font-bold text-ink">{plural(docs.length, "deck")}</strong> · {plural(pages, "slide page")} · {plural(chunks, "chunk")}</>
            : "The slides that Synapse answers from."}
        </p>
        <p className="mt-1 max-w-[60ch] text-small text-ink-3">
          No silent failures: every page is indexed, flagged with a reason, or marked as a duplicate.
        </p>
      </header>

      {error != null && <ErrorState className="mt-6" error={error} onRetry={refresh} />}

      {DEMO && (
        <div className="mt-6 flex flex-wrap items-start gap-3 rounded-md bg-sunk p-4 text-small text-ink-2">
          <Badge>Read-only in this demo</Badge>
          <p className="min-w-0 flex-1 basis-64">{DEMO_OFF}</p>
        </div>
      )}

      {!DEMO && (
        <Card className="mt-6 space-y-3 p-4 md:p-5">
          <h2 className="font-sans text-h3">Upload</h2>
          <label className="block text-small text-ink-2">
            <span className="sr-only">Choose PDF or DOCX files</span>
            <input
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              className="block w-full text-small file:mr-3 file:min-h-11 file:rounded-md file:border file:border-rule-strong file:bg-raised file:px-3 file:font-semibold file:text-ink"
            />
          </label>
          <Button onClick={upload} disabled={!files.length || busy}>
            <Upload size={18} strokeWidth={1.75} aria-hidden />
            {busy ? "Uploading..." : `Upload ${files.length || ""} ${files.length === 1 ? "file" : "files"}`}
          </Button>
          <p className="text-small text-ink-3">PDF or DOCX. Files are indexed one at a time in the background.</p>
          {jobs.map((j) => <JobRow key={j.job_id} job={j} />)}
        </Card>
      )}

      <section aria-label="Indexed decks" className="mt-6">
        {docs === null && error == null && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-hidden>
            {Array.from({ length: 7 }, (_, i) => (
              <Card key={i} className="space-y-3 p-4">
                <Skeleton className="aspect-[1100/619] w-full rounded-md" />
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-5 w-4/5" />
                <Skeleton className="h-4 w-1/2" />
              </Card>
            ))}
          </div>
        )}

        {docs?.length === 0 && (
          <EmptyState title="No documents yet">Upload your slides above, and they will appear here once indexed.</EmptyState>
        )}

        {!!docs?.length && (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {docs.map((d, i) => <DeckCard key={d.doc_id} doc={d} eager={i < 3} onDelete={DEMO ? undefined : () => remove(d)} />)}
            <li className="rounded-lg border border-dashed border-rule-strong p-5 lg:col-span-2 lg:self-start">
              <h2 className="font-sans text-h3">What these numbers mean</h2>
              <dl className="mt-3 grid gap-3 text-small sm:grid-cols-[auto_minmax(0,1fr)] sm:gap-x-4">
                <dt className="font-semibold">Chunk</dt>
                <dd className="text-ink-2">One searchable piece, usually one slide. Search and citations work on these.</dd>
                <dt className="font-semibold">Repeated slide</dt>
                <dd className="text-ink-2">A copy or near-copy of another slide. It is skipped, so search results do not repeat it.</dd>
                <dt className="font-semibold">Needs OCR</dt>
                <dd className="text-ink-2">A page with no readable text, such as a diagram. It is reported, not silently dropped, but it cannot be searched yet.</dd>
              </dl>
            </li>
          </ul>
        )}
      </section>
    </div>
  );
}

function DeckCard({ doc: d, eager, onDelete }: { doc: DocumentRow; eager?: boolean; onDelete?: () => void }) {
  const name = deckName(d.file_name);
  // The unit already shows as a badge, so the title starts after it. The spelling is the file's own.
  const title = d.unit && name.startsWith(`${d.unit}${DECK_SEP}`) ? name.slice(d.unit.length + DECK_SEP.length) : name;
  const firstPage = DEMO ? `/demo/pages/${d.doc_id}/1.webp` : `/pages/${d.doc_id}/1/image`;
  return (
    <li>
      <Card className="flex h-full flex-col gap-3 p-4">
        <SlideImage slide={{ label: `${d.file_name}, p.1`, image_url: firstPage }} sizes="(min-width: 1024px) 340px, (min-width: 640px) 45vw, 100vw" eager={eager} />
        <div className="flex flex-wrap items-center gap-2">
          {d.unit && <Badge>{d.unit}</Badge>}
          {d.status !== "active" && <Badge tone="warn">{d.status}</Badge>}
        </div>
        <h2 className="font-sans text-h3" title={d.file_name}>{title}</h2>
        <p className="font-mono text-mono text-ink-2">{plural(d.pages_total, "page")} · {plural(d.chunks, "chunk")}</p>
        {(d.pages_duplicate > 0 || d.pages_flagged > 0) && (
          <ul className="space-y-0.5 text-small text-ink-3">
            {d.pages_duplicate > 0 && <li>{plural(d.pages_duplicate, "repeated slide")} skipped</li>}
            {d.pages_flagged > 0 && <li>{plural(d.pages_flagged, "page")} flagged: {d.pages_flagged === 1 ? "needs" : "need"} OCR</li>}
          </ul>
        )}
        <div className="mt-auto flex items-center justify-between gap-2 pt-1">
          {d.unit
            ? (
              <Link href={`/ask?unit=${encodeURIComponent(d.unit)}`} className="inline-flex min-h-11 items-center gap-1.5 font-semibold underline decoration-rule-strong underline-offset-4 hover:decoration-ink">
                Ask this unit
                <ArrowRight size={16} strokeWidth={1.75} aria-hidden />
              </Link>
            )
            : <span />}
          {onDelete && (
            <Button variant="ghost" size="sm" onClick={onDelete} aria-label={`Delete ${d.file_name}`} className="text-wrong">
              <Trash2 size={16} strokeWidth={1.5} aria-hidden />
              Delete
            </Button>
          )}
        </div>
      </Card>
    </li>
  );
}

function JobRow({ job }: { job: Job }) {
  const r = job.report;
  const colour = { queued: "text-ink-3", running: "text-accent-ink", done: "text-correct", failed: "text-wrong" }[job.state];
  return (
    <div className="rounded-md border p-3 text-small">
      <p>
        <span className="font-semibold">{job.file_name}</span>{" "}
        <span className={colour}>{job.state === "running" ? "indexing..." : job.state}</span>
        {r?.status && r.status !== "failed" && (
          <span className="text-ink-2">
            {" "}· {r.status.replace("_", " ")} · {r.pages_with_text}/{r.pages_total} pages with text · {r.chunks_created} chunks
            {r.pages_duplicate ? ` · ${r.pages_duplicate} duplicate pages` : ""} · {r.seconds?.toFixed(1)} s
          </span>
        )}
      </p>
      {r?.message && job.state === "failed" && <Notice>{r.message}</Notice>}
      {!!r?.flagged_pages?.length && (
        <p className="text-warn">
          Flagged: {r.flagged_pages.map(([p, why]) => `page ${p ?? "?"} (${why})`).join(", ")}
        </p>
      )}
      {r?.warnings?.map((w) => <p key={w} className="text-warn">{w}</p>)}
    </div>
  );
}
