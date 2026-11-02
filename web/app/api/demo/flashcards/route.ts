// POST /api/demo/flashcards: generate_flashcards() in flashcards.py. The browser stores the cards (localStorage).
import { jsonItems, pickSlides, sourcesBlock, validateCard, type Source } from "@/lib/demo/core";
import { chunks, complete, DemoError, groqKey, imageUrl, jsonError, meta } from "@/lib/demo/server";

export const maxDuration = 120;

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => null);
    const n = body?.n ?? 10;
    const f = meta.flashcards;
    if (!Number.isInteger(n) || n < 1 || n > f.max_cards) throw new DemoError(422, `n must be 1..${f.max_cards}, got ${n}`);
    groqKey();
    let sources: Source[];
    try {
      sources = pickSlides(chunks, body?.units, meta, body?.seed ?? 0);
    } catch (e) {
      throw new DemoError(422, e instanceof Error ? e.message : String(e));
    }
    const user = `Slides:\n\n${sourcesBlock(sources)}\n\nMake ${n} flashcards.`;
    const reply = await complete("groq", meta.prompts.cards_system, user, f.max_tokens, meta.llm.temperature, true);
    const items = jsonItems(reply, "cards");
    if (items === null) return Response.json({ cards: [], rejected: ["reply was not JSON with a 'cards' list"] });

    const cards: Record<string, unknown>[] = [];
    const rejected: string[] = [];
    const seen = new Set<string>();
    items.forEach((item, i) => {
      const d = validateCard(item);
      if (typeof d === "string") return void rejected.push(`card ${i + 1}: ${d}`);
      const s = sources.find((x) => x.n === d.source);
      if (!s) return void rejected.push(`card ${i + 1}: source ${d.source} is not one of the slides`);
      const key = d.front.toLowerCase().split(/\s+/).filter(Boolean).join(" ");
      if (seen.has(key)) return void rejected.push(`card ${i + 1}: repeats an earlier card`);
      seen.add(key);
      cards.push({
        front: d.front,
        back: d.back,
        file_name: s.chunk.file_name,
        page: s.chunk.page_start,
        doc_id: s.chunk.doc_id,
        chunk_id: s.chunk.id,
        unit: s.chunk.unit,
        image_url: imageUrl(s.chunk),
      });
    });
    return Response.json({ cards: cards.slice(0, n), rejected });
  } catch (e) {
    return jsonError(e);
  }
}
