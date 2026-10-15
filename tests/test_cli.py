import docx
import pytest
import yaml

from cornerstone import SCHEMA_VERSION, cli
from cornerstone.embeddings import Embedder
from cornerstone.index.metadata_store import MetadataStore


@pytest.fixture(scope="module")
def shared_embedder(cfg):
    return Embedder(cfg)


@pytest.fixture
def env(cfg, shared_embedder, tmp_path, monkeypatch):
    c = {**cfg, "paths": {"raw_dir": str(tmp_path / "raw"), "index_dir": str(tmp_path / "index"),
                         "image_dir": str(tmp_path / "images")}}
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


def _make_v01_index(index_dir):
    import sqlite3
    index_dir.mkdir(parents=True)
    con = sqlite3.connect(index_dir / cli.DB_FILE)
    con.execute("CREATE TABLE documents(doc_id INTEGER PRIMARY KEY, file_name TEXT)")
    con.commit()
    con.close()


def test_v01_index_fails_loudly_and_rebuild_keeps_the_old_folder(env, capsys, monkeypatch):
    base, f, tmp = env
    _make_v01_index(tmp / "index")
    assert cli.main(base + ["stats"]) == 1
    err = capsys.readouterr().err
    assert "IndexVersionMismatch" in err and "cli rebuild" in err
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    assert cli.main(base + ["rebuild", str(f)]) == 1           # no --yes, not interactive: refuses
    assert "not rebuilt" in capsys.readouterr().err and not (tmp / "index.v1.bak").exists()
    assert cli.main(base + ["rebuild", str(f), "--yes"]) == 0
    out = capsys.readouterr().out
    assert "old index kept at" in out and "[indexed] scheduling.docx" in out
    assert (tmp / "index.v1.bak" / cli.DB_FILE).is_file()     # old database moved, not deleted
    assert cli.main(base + ["stats"]) == 0
    assert "documents: 1 active" in capsys.readouterr().out
    assert cli.main(base + ["rebuild", str(f), "--yes"]) == 0  # second rebuild: backup name does not clash
    assert (tmp / f"index.v{SCHEMA_VERSION}.bak").is_dir()       # named after the version being replaced


def test_rebuild_with_no_files_fails(env, capsys):
    base, _, tmp = env
    empty = tmp / "empty"
    empty.mkdir()
    assert cli.main(base + ["rebuild", str(empty), "--yes"]) == 1
    assert "no .pdf/.docx" in capsys.readouterr().err


def test_search_unit_and_file_filters(env, capsys):
    base, f, tmp = env
    assert cli.main(base + ["ingest", str(f)]) == 0               # scheduling.docx has no unit
    capsys.readouterr()
    assert cli.main(base + ["search", "round robin", "--unit", "Unit 4"]) == 0
    assert "no results" in capsys.readouterr().out
    assert cli.main(base + ["search", "round robin", "--file", "scheduling.docx"]) == 0
    assert "scheduling.docx" in capsys.readouterr().out
    assert cli.main(base + ["search", "round robin", "--file", "ghost.pdf"]) == 0
    io = capsys.readouterr()
    assert "not indexed: ghost.pdf" in io.err and "no results" in io.out


def test_compact_command(env, capsys, monkeypatch):
    base, f, tmp = env
    assert cli.main(base + ["ingest", str(f)]) == 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    assert cli.main(base + ["compact"]) == 1 and "not compacted" in capsys.readouterr().err
    assert cli.main(base + ["compact", "--yes"]) == 0
    assert "0 deleted chunk rows" in capsys.readouterr().out


def test_ask_streams_answer_with_sources_and_abstains(env, capsys, monkeypatch):
    from cornerstone import llm

    base, f, tmp = env
    assert cli.main(base + ["ingest", str(f)]) == 0
    capsys.readouterr()
    fake = llm.FakeProvider(["Round robin gives each process a fixed time quantum [1]. It never starves anyone [9].",
                             "NOT_IN_NOTES"])            # reply i for call i
    monkeypatch.setattr(llm, "make_provider", lambda cfg, name=None, env=None, client=None: fake)
    assert cli.main(base + ["ask", "What is round robin scheduling?", "--mode", "2-mark"]) == 0
    out = capsys.readouterr().out
    assert "fixed time quantum [1]" in out and "[1] scheduling - CPU scheduling" in out
    assert "invalid references removed: [9]" in out
    assert cli.main(base + ["ask", "Who wrote Hamlet?"]) == 0
    assert "Not in your notes." in capsys.readouterr().out
    assert cli.main(base + ["ask", "   "]) == 1
