/** Coloured message box; every error the API returns is shown with one of these, never swallowed. */
export default function Notice({ kind = "error", children }: { kind?: "error" | "warn" | "info"; children: React.ReactNode }) {
  const style = {
    error: "border-red-300 bg-red-50 text-red-800",
    warn: "border-amber-300 bg-amber-50 text-amber-900",
    info: "border-slate-300 bg-slate-50 text-slate-700",
  }[kind];
  return <div className={`rounded border px-3 py-2 text-sm ${style}`}>{children}</div>;
}
