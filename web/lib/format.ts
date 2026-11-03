// Display helpers only: they change how a name looks, never what it refers to.

/** "Unit 4_Storage management_ Disk Schduling.pdf" -> "Unit 4 · Storage management · Disk Schduling" (spelling kept). */
export function deckName(file: string): string {
  return file
    .replace(/\.(pdf|docx)$/i, "")
    .split("_")
    .map((part) => part.trim())
    .filter(Boolean)
    .join(" · ");
}

/** Splits the API's source label "file, p.15" or "file, pp.1-2" into a readable deck name and its page. */
export function splitLabel(label: string): { deck: string; page: string | null } {
  const m = label.match(/^(.*),\s*(pp?\.\s*[\d\-–]+)$/);
  return m ? { deck: deckName(m[1]), page: m[2] } : { deck: deckName(label), page: null };
}

export const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
