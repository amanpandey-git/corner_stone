// POST /api/demo/quiz: generate_quiz() in quiz.py, in the JSON of /quiz in api.py.
import { jsonItems, pickSlides, sourcesBlock, validateMcq, type Mcq, type Source } from "@/lib/demo/core";
import { chunks, complete, DemoError, groqKey, jsonError, meta, quizSourceJson } from "@/lib/demo/server";

export const maxDuration = 120;

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => null);
    const n = body?.n ?? 5;
    const q = meta.quiz;
    if (!Number.isInteger(n) || n < 1 || n > q.max_questions) throw new DemoError(422, `n must be 1..${q.max_questions}, got ${n}`);
    groqKey();
    let sources: Source[];
    try {
      sources = pickSlides(chunks, body?.units, meta, body?.seed ?? 0);
    } catch (e) {
      throw new DemoError(422, e instanceof Error ? e.message : String(e));
    }

    const questions: { mcq: Mcq; source: Source }[] = [];
    const rejected: string[] = [];
    const seen = new Set<string>();
    let generated = 0;
    let attempts = 0;
    while (questions.length < n && attempts < q.max_attempts) {
      const missing = n - questions.length;
      let user = `Slides:\n\n${sourcesBlock(sources)}\n\nWrite ${missing} questions.`;
      if (questions.length) user += ` Do not repeat these questions:\n${questions.map((x) => `- ${x.mcq.question}`).join("\n")}`;
      attempts++;
      const reply = await complete("groq", meta.prompts.quiz_system, user, q.max_tokens, meta.llm.temperature, true);
      const items = jsonItems(reply, "questions");
      if (items === null) {
        rejected.push(`attempt ${attempts}: reply was not JSON with a 'questions' list`);
        continue;
      }
      const ok: { mcq: Mcq; source: Source }[] = [];
      items.forEach((item, i) => {
        const label = `item ${generated + 1 + i}`;
        const mcq = validateMcq(item);
        if (typeof mcq === "string") return void rejected.push(`${label}: ${mcq}`);
        const source = sources.find((s) => s.n === mcq.source);
        if (!source) return void rejected.push(`${label}: source ${mcq.source} is not one of the slides`);
        const key = mcq.question.toLowerCase().split(/\s+/).filter(Boolean).join(" ");
        if (seen.has(key)) return void rejected.push(`${label}: repeats an earlier question`);
        seen.add(key);
        ok.push({ mcq, source });
      });
      generated += items.length;
      questions.push(...ok.slice(0, missing));
    }
    return Response.json({
      requested: n,
      generated,
      attempts,
      rejected,
      questions: questions.map(({ mcq, source }) => ({
        question: mcq.question,
        options: mcq.options,
        answer: mcq.answer,
        explanation: mcq.explanation,
        source: quizSourceJson(source),
      })),
    });
  } catch (e) {
    return jsonError(e);
  }
}
