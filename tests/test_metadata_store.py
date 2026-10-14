import pytest

from cornerstone import Chunk, Document, Page
from cornerstone.index.metadata_store import MetadataStore


def make_doc(name="a.pdf", sha="h1"):
    return Document(file_name=name, sha256=sha, file_type="pdf")


def make_pages(n_ok=3, n_flag=1):
    pages = [Page(i + 1, f"text of page {i + 1}") for i in range(n_ok)]
    pages += [Page(n_ok + j + 1, "", status="needs_ocr", reason="scanned image") for j in range(n_flag)]
    return pages


def make_chunks(n=4, name="a.pdf"):
    return [Chunk(chunk_id=0, doc_id=0, file_name=name, text=f"chunk {i} words", chunk_index=i,
                  token_count=3, section_heading=f"H{i}", page_start=i + 1, page_end=i + 1) for i in range(n)]


@pytest.fixture
def store(tmp_path):
    s = MetadataStore(tmp_path / "meta.sqlite")
    yield s
    s.close()


def test_insert_and_read_back(store):
    doc = make_doc()
    ids = store.add_document(doc, make_pages(), make_chunks())
    assert len(ids) == 4 and ids == sorted(ids) and doc.doc_id > 0
    store.activate(doc.doc_id)
    got = store.get_chunks(ids)
    assert set(got) == set(ids)
    c = got[ids[2]]
    assert (c.file_name, c.text, c.section_heading, c.page_start, c.chunk_index) == ("a.pdf", "chunk 2 words", "H2", 3, 2)
    d = store.get_document(doc.doc_id)
    assert (d.n_pages, d.n_pages_text, d.n_pages_flagged, d.n_chunks, d.status) == (4, 3, 1, 4, "active")


def test_find_by_hash_and_name(store):
    doc = make_doc()
    store.add_document(doc, make_pages(), make_chunks())
    assert store.find_by_hash("h1") is None                  # pending does not count as ingested
    assert store.find_active_by_name("a.pdf") is None
    store.activate(doc.doc_id)
    assert store.find_by_hash("h1").doc_id == doc.doc_id
    assert store.find_active_by_name("a.pdf").sha256 == "h1"
    assert store.find_by_hash("nope") is None and store.find_active_by_name("b.pdf") is None


def test_replace_marks_old_document_and_hides_its_chunks(store):
    old = make_doc(sha="v1")
    old_ids = store.add_document(old, make_pages(), make_chunks())
    store.activate(old.doc_id)
    new = make_doc(sha="v2")
    new_ids = store.add_document(new, make_pages(), make_chunks(2))
    store.activate(new.doc_id, replaces=old.doc_id)           # one transaction
    assert store.get_document(old.doc_id).status == "replaced"
    assert store.find_active_by_name("a.pdf").doc_id == new.doc_id
    assert store.get_chunks(old_ids) == {}                    # old chunks never returned
    assert set(store.get_chunks(new_ids)) == set(new_ids)
    assert store.find_by_hash("v1") is None
    assert min(new_ids) > max(old_ids)                        # ids never reused


def test_mark_replaced_standalone(store):
    doc = make_doc()
    ids = store.add_document(doc, make_pages(), make_chunks())
    store.activate(doc.doc_id)
    store.mark_replaced(doc.doc_id)
    assert store.get_chunks(ids) == {} and store.stats()["chunks_deleted"] == 4
    with pytest.raises(ValueError):
        store.mark_replaced(doc.doc_id)                       # already retired


def test_crash_between_add_and_activate_leaves_pending(tmp_path):
    path = tmp_path / "meta.sqlite"
    s = MetadataStore(path)
    doc = make_doc()
    ids = s.add_document(doc, make_pages(), make_chunks())
    s.close()                                                 # "crash": process dies before activate()
    s2 = MetadataStore(path)
    d = s2.get_document(doc.doc_id)
    assert d.status == "pending"
    assert s2.get_chunks(ids) == {}                           # pending chunks are not searchable
    assert s2.find_by_hash("h1") is None
    assert any("interrupted" in p for p in s2.check_sync(set(ids)))
    s2.discard_pending(doc.doc_id)
    assert s2.get_document(doc.doc_id).status == "abandoned"
    assert s2.check_sync(set(ids)) == []
    s2.close()


def test_failed_write_is_rolled_back_completely(store):
    doc = make_doc()
    bad = make_chunks(3)
    bad[2].text = None                                        # violates NOT NULL on the 3rd insert
    with pytest.raises(Exception):
        store.add_document(doc, make_pages(), bad)
    assert store.list_documents("pending") == []
    st = store.stats()
    assert st["chunks_pending"] == 0 and st["documents_pending"] == 0 and st["pages_total"] == 0


def test_check_sync_detects_mismatch_with_index(store):
    doc = make_doc()
    ids = store.add_document(doc, make_pages(), make_chunks())
    store.activate(doc.doc_id)
    assert store.check_sync(set(ids)) == []
    missing = store.check_sync(set(ids[:-1]))                 # vector lost from the index
    assert len(missing) == 1 and "no vector in the index" in missing[0]
    orphan = store.check_sync(set(ids) | {9999})              # vector with no SQLite row
    assert len(orphan) == 1 and "no row in SQLite" in orphan[0]
    store.mark_replaced(doc.doc_id)                           # deleted rows may stay in the index
    assert store.check_sync(set(ids)) == []


def test_stats_and_flagged_pages(store):
    doc = make_doc()
    store.add_document(doc, make_pages(3, 2), make_chunks())
    store.activate(doc.doc_id)
    st = store.stats()
    assert (st["documents"], st["pages_total"], st["pages_with_text"], st["pages_flagged"]) == (1, 5, 3, 2)
    assert st["chunks_active"] == 4
    assert st["flagged_pages"][0] == {"file_name": "a.pdf", "page_no": 4, "status": "needs_ocr",
                                      "reason": "scanned image"}


def test_cannot_have_two_active_versions_of_one_name(store):
    a, b = make_doc(sha="v1"), make_doc(sha="v2")
    store.add_document(a, make_pages(), make_chunks())
    store.add_document(b, make_pages(), make_chunks())
    store.activate(a.doc_id)
    with pytest.raises(Exception):
        store.activate(b.doc_id)                              # unique index on active file_name
    assert store.get_document(b.doc_id).status == "pending"   # failed activate rolled back
