import docx
import pytest
import yaml

from cornerstone import cli
from cornerstone.embeddings import Embedder
from cornerstone.index.metadata_store import MetadataStore


@pytest.fixture(scope="module")
def shared_embedder(cfg):
    return Embedder(cfg)


@pytest.fixture
def env(cfg, shared_embedder, tmp_path, monkeypatch):
    c = {**cfg, "paths": {"raw_dir": str(tmp_path / "raw"), "index_dir": str(tmp_path / "index")}}
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(yaml.safe_dump(c), encoding="utf-8")
    monkeypatch.setattr(cli, "Embedder", lambda _cfg: shared_embedder)   # model loads once per test run
    f = tmp_path / "scheduling.docx"
    d = docx.Document()
    d.add_heading("CPU scheduling", level=1)
    d.add_paragraph("Round robin scheduling gives each process a fixed time quantum in turn. " * 6)
    d.save(f)
    return ["--config", str(cfg_file)], f, tmp_path


def test_ingest_search_stats_roundtrip(env, capsys):
    base, f, tmp = env
    assert cli.main(base + ["ingest", str(f)]) == 0
    assert "[indexed] scheduling.docx" in capsys.readouterr().out
    assert cli.main(base + ["ingest", str(f)]) == 0
    assert "skipped_duplicate" in capsys.readouterr().out
    assert cli.main(base + ["search", "what is round robin?", "--k", "3"]) == 0
    out = capsys.readouterr().out
    assert "scheduling.docx" in out and "paragraphs" in out and "CPU scheduling" in out
    assert cli.main(base + ["stats"]) == 0
    out = capsys.readouterr().out
    assert "documents: 1 active" in out and "dim 384" in out


def test_failures_and_blank_query_have_nonzero_exit(env, capsys):
    base, f, tmp = env
    bad = tmp / "x.txt"
    bad.write_text("hi")
    assert cli.main(base + ["ingest", str(bad)]) == 1
    assert "UnsupportedFileType" in capsys.readouterr().out
    assert cli.main(base + ["search", "   "]) == 1
    assert "empty" in capsys.readouterr().err.lower()


def test_search_on_empty_index_says_so(env, capsys):
    base, _, _ = env
    assert cli.main(base + ["search", "anything"]) == 0
    assert "no results" in capsys.readouterr().out


def test_pending_ingest_is_reported_and_not_discarded_without_consent(env, capsys, monkeypatch):
    base, f, tmp = env
    assert cli.main(base + ["ingest", str(f)]) == 0
    # fabricate an interrupted ingest directly in the store
    from cornerstone import Chunk, Document, Page
    s = MetadataStore(tmp / "index" / cli.DB_FILE)
    s.add_document(Document("ghost.pdf", "deadbeef", "pdf"), [Page(1, "t")],
                   [Chunk(0, 0, "ghost.pdf", "t", 0, 1)])
    s.close()
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    capsys.readouterr()
    assert cli.main(base + ["stats"]) == 0
    io = capsys.readouterr()
    assert "interrupted" in io.err and "not discarded" in io.err
    assert "1 pending" in io.out
    assert cli.main(base + ["stats", "--yes"]) == 0
    io = capsys.readouterr()
    assert "discarded interrupted ingest of ghost.pdf" in io.err
    assert cli.main(base + ["stats"]) == 0
    assert "0 pending" in capsys.readouterr().out
