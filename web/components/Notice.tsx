/** Coloured message box; every error the API returns is shown with one of these, never swallowed. */
export default function Notice({ kind = "error", children }: { kind?: "error" | "warn" | "info"; children: React.ReactNode }) {
  const style = {
    error: "bg-wrong-bg text-wrong",
    warn: "bg-warn-bg text-warn",
    info: "border-rule-strong bg-paper text-ink-2",
  }[kind];
  return <div className={`rounded border px-3 py-2 text-sm ${style}`}>{children}</div>;
}
