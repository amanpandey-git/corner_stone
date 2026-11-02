// GET /api/demo/health: the JSON of GET /health in api.py.
import { connection } from "next/server";
import docs from "@/public/demo/docs.json";
import { meta } from "@/lib/demo/server";

export async function GET() {
  await connection();     // with cacheComponents a GET is otherwise prerendered, freezing the key check at build time
  return Response.json({
    status: "ok",
    documents: docs.length,
    chunks: meta.n_chunks,
    schema_version: meta.schema_version,
    llm_provider: "groq",
    llm_key_present: !!process.env.GROQ_API_KEY,
    rerank: false,
    hybrid: false,
  });
}
