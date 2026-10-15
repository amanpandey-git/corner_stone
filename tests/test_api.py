import copy
import json
import time

import pytest
from fastapi.testclient import TestClient

from cornerstone import LLMUnavailable
from cornerstone.api import create_app
from cornerstone.embeddings import Embedder
from cornerstone.llm import FakeProvider

from conftest import SAMPLES

PDF = SAMPLES / "Unit 5_Part 2_System Protection.pdf"


class Replies:
    """Provider factory for tests: one FakeProvider per role, replies set per test."""

    def __init__(self):
        self.answer = FakeProvider(["Least privilege grants only the rights a task needs [1]."])
        self.judge = FakeProvider(['{"unsupported": []}'], name="judge")
        self.down = False

    def __call__(self, cfg, name=None):
        if self.down:
            raise LLMUnavailable("GROQ_API_KEY is not set")
        return self.judge if name == cfg["answer"]["judge_provider"] else self.answer


@pytest.fixture(scope="module")
def embedder(cfg):
    return Embedder(cfg)


@pytest.fixture(scope="module")
def env(cfg, embedder, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("api")
    c = copy.deepcopy(cfg)
    c["paths"] = {"raw_dir": str(tmp / "raw"), "index_dir": str(tmp / "index"), "image_dir": str(tmp / "images"),
                  "cache_dir": str(tmp / "cache"), "study_db": str(tmp / "study.sqlite")}
    replies = Replies()
    client = TestClient(create_app(c, provider_factory=replies, embedder=embedder))
    r = client.post("/documents", files=[("files", (PDF.name, PDF.read_bytes(), "application/pdf"))])
    assert r.status_code == 202
    job_id = r.json()["jobs"][0]["job_id"]
    for _ in range(300):
        job = client.get(f"/documents/jobs/{job_id}").json()
        if job["state"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert job["state"] == "done", job
    return client, replies


def test_health_and_documents(env):
    client, _ = env
    h = client.get("/health").json()
    assert h["status"] == "ok" and h["documents"] == 1 and h["chunks"] > 0 and h["schema_version"] == 3
    assert "key" not in json.dumps(h).replace("llm_key_present", "")
    docs = client.get("/documents").json()
    assert docs[0]["file_name"] == PDF.name and docs[0]["unit"] == "Unit 5" and docs[0]["chunks"] > 0


def test_search_returns_sources_with_images(env):
    client, _ = env
    res = client.get("/search", params={"q": "principle of least privilege", "k": 3}).json()
    assert len(res) == 3 and res[0]["rank"] == 1 and res[0]["file_name"] == PDF.name
    img = client.get(res[0]["image_url"])
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    assert client.get("/search", params={"q": "access matrix", "unit": "Unit 9"}).json() == []
    assert client.get("/search", params={"q": "   "}).status_code == 422
    assert client.get("/search", params={"q": "x", "k": 0}).status_code == 422
    assert client.get("/pages/1/999/image").status_code == 404


def test_ask_json_and_validation(env):
    client, replies = env
    a = client.post("/ask", json={"question": "What is least privilege?", "mode": "2-mark", "check": True}).json()
    assert not a["abstained"] and a["citations"][0]["refs"] == [1] and a["unsupported"] == []
    cited = [s for s in a["sources"] if s["cited"]]
    assert cited[0]["n"] == 1 and cited[0]["image_url"].startswith("/pages/")
    assert client.post("/ask", json={"question": " "}).status_code == 422
    assert client.post("/ask", json={"question": "x", "mode": "essay"}).status_code == 422


def test_ask_stream_event_order(env):
    client, _ = env
    with client.stream("POST", "/ask/stream", json={"question": "What is least privilege?"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    kinds = [line.split(": ", 1)[1] for line in body.splitlines() if line.startswith("event: ")]
    assert kinds[0] == "delta" and kinds[-1] == "final" and set(kinds) == {"delta", "final"}
    final = json.loads(body.strip().split("data: ")[-1])
    assert final["text"].endswith("[1].")


def test_llm_unavailable_is_503_without_key_text(env):
    client, replies = env
    replies.down = True
    try:
        r = client.post("/ask", json={"question": "What is least privilege?"})
        assert r.status_code == 503 and "GROQ_API_KEY is not set" in r.json()["detail"]
    finally:
        replies.down = False


def test_quiz_and_flashcards_loop(env):
    client, replies = env
    item = {"question": "What does a protection domain specify?", "options": ["A set of access rights", "A disk",
            "A CPU core", "A network port"], "answer": 0, "explanation": "A domain is a set of access rights.",
            "source": 1}
    replies.answer = FakeProvider([json.dumps({"questions": [item]})])
    qz = client.post("/quiz", json={"n": 1, "units": ["Unit 5"]}).json()
    q = qz["questions"][0]
    assert q["answer"] == 0 and q["source"]["file_name"] == PDF.name and q["source"]["image_url"]
    assert client.post("/quiz", json={"n": 1, "units": ["Unit 9"]}).status_code == 422

    made = client.post("/flashcards/from-quiz", json=q).json()
    assert made["created"] and made["card"]["origin"] == "quiz" and made["card"]["unit"] == "Unit 5"
    assert client.post("/flashcards/from-quiz", json=q).json()["created"] is False

    replies.answer = FakeProvider([json.dumps({"cards": [{"front": "Access matrix", "back": "Rows are domains.",
                                                          "source": 1}]})])
    gen = client.post("/flashcards/generate", json={"n": 1}).json()
    assert len(gen["created"]) == 1
    due = client.get("/flashcards/due").json()
    assert len(due["cards"]) == 2 and due["stats"]["cards"] == 2
    cid = due["cards"][0]["card_id"]
    rev = client.post(f"/flashcards/{cid}/review", json={"grade": 4}).json()
    assert rev["reps"] == 1 and rev["interval"] == 1
    assert client.post("/flashcards/9999/review", json={"grade": 4}).status_code == 404
    assert client.post(f"/flashcards/{cid}/review", json={"grade": 9}).status_code == 422


def test_upload_rejects_wrong_type_and_delete_hides_document(env):
    client, _ = env
    r = client.post("/documents", files=[("files", ("notes.txt", b"hello", "text/plain"))])
    assert r.status_code == 415
    assert client.get("/documents/jobs/nope").status_code == 404
    doc_id = client.get("/documents").json()[0]["doc_id"]
    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get("/documents").json() == []
    assert client.get("/search", params={"q": "least privilege"}).json() == []
    assert client.delete(f"/documents/{doc_id}").status_code == 404
