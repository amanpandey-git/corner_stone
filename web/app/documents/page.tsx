"use client";

import { useCallback, useEffect, useState } from "react";
import Notice from "@/components/Notice";
import { del, errorText, getJSON, uploadFiles, type DocumentRow, type Job } from "@/lib/api";

const POLL_MS = 1000;

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentRow[] | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    getJSON<DocumentRow[]>("/documents").then(
      (d) => { setDocs(d); setError(null); },
      (e) => setError(errorText(e)),
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
        setError(errorText(e));
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
      setError(errorText(e));
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
      setError(errorText(e));
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Documents</h1>
      {error && <Notice>{error}</Notice>}

      <section className="space-y-3 rounded-lg border bg-white p-4">
        <h2 className="font-semibold">Upload</h2>
        <input
          type="file"
          multiple
          accept=".pdf,.docx"
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          className="block text-sm file:mr-3 file:rounded file:border-0 file:bg-slate-200 file:px-3 file:py-1"
        />
        <button
          onClick={upload}
          disabled={!files.length || busy}
          className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-40"
        >
          {busy ? "Uploading..." : `Upload ${files.length || ""} file${files.length === 1 ? "" : "s"}`}
        </button>
        <p className="text-xs text-slate-500">PDF or DOCX. Files are indexed one at a time in the background.</p>
        {jobs.map((j) => <JobRow key={j.job_id} job={j} />)}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Indexed</h2>
        {docs === null ? (
          !error && <p className="text-sm text-slate-500">Loading...</p>
        ) : docs.length === 0 ? (
          <Notice kind="info">No documents yet. Upload your slides above.</Notice>
        ) : (
          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="p-2">File</th>
                  <th className="p-2">Unit</th>
                  <th className="p-2 text-right">Pages</th>
                  <th className="p-2 text-right">Flagged</th>
                  <th className="p-2 text-right">Duplicates</th>
                  <th className="p-2 text-right">Chunks</th>
                  <th className="p-2" />
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.doc_id} className="border-t">
                    <td className="p-2">{d.file_name}</td>
                    <td className="p-2">{d.unit ?? "-"}</td>
                    <td className="p-2 text-right">{d.pages_total}</td>
                    <td className="p-2 text-right">{d.pages_flagged}</td>
                    <td className="p-2 text-right">{d.pages_duplicate}</td>
                    <td className="p-2 text-right">{d.chunks}</td>
                    <td className="p-2 text-right">
                      <button onClick={() => remove(d)} className="text-red-700 hover:underline">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function JobRow({ job }: { job: Job }) {
  const r = job.report;
  const colour = { queued: "text-slate-500", running: "text-blue-700", done: "text-green-700", failed: "text-red-700" }[job.state];
  return (
    <div className="rounded border p-2 text-sm">
      <p>
        <span className="font-medium">{job.file_name}</span>{" "}
        <span className={colour}>{job.state === "running" ? "indexing..." : job.state}</span>
        {r?.status && r.status !== "failed" && (
          <span className="text-slate-600">
            {" "}· {r.status.replace("_", " ")} · {r.pages_with_text}/{r.pages_total} pages with text · {r.chunks_created} chunks
            {r.pages_duplicate ? ` · ${r.pages_duplicate} duplicate pages` : ""} · {r.seconds?.toFixed(1)} s
          </span>
        )}
      </p>
      {r?.message && job.state === "failed" && <p className="text-red-700">{r.message}</p>}
      {!!r?.flagged_pages?.length && (
        <p className="text-amber-800">
          Flagged: {r.flagged_pages.map(([p, why]) => `page ${p ?? "?"} (${why})`).join(", ")}
        </p>
      )}
      {r?.warnings?.map((w) => <p key={w} className="text-amber-800">{w}</p>)}
    </div>
  );
}
