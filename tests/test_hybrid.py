import pytest

from cornerstone import Chunk, Document, Page, SearchFilters
from cornerstone.hybrid import fts_query, keyword_search, rrf_merge
from cornerstone.index.metadata_store import MetadataStore


# ------------------------------------------------------------------ keyword search
@pytest.fixture
def store(tmp_path):
    s = MetadataStore(tmp_path / "m.sqlite")
    docs = {
        "Unit 4_Disk.pdf": ["C-LOOK serves requests only while moving towards the last request.",
                            "Seek time is the time taken by the disk arm to locate the desired track."],
        "Unit 5_Protection.pdf": ["The setuid bit switches the domain to the owner of the file."],
    }
    for name, texts in docs.items():
        d = Document(name, name, "pdf", unit=name.split("_")[0])
        chunks = [Chunk(0, 0, name, t, i, 10, page_start=i + 1, page_end=i + 1, context_header=f"{name[:-4]} > T")
                  for i, t in enumerate(texts)]
        s.add_document(d, [Page(i + 1, t) for i, t in enumerate(texts)], chunks)
        s.activate(d.doc_id)
    yield s
    s.close()


def test_fts_query_quotes_tokens_and_drops_stopwords():
    assert fts_query('What is the "C-LOOK" algorithm?') == '"c" OR "look" OR "algorithm"'
    assert fts_query("what is the") == "" and fts_query("?!") == ""


def test_exact_rare_word_found_first(store):
    hits = keyword_search("how does setuid work", 5, store)
    assert len(hits) == 1
    assert store.get_chunks([hits[0][0]])[hits[0][0]].file_name == "Unit 5_Protection.pdf"


def test_scores_descend_and_k_limits(store):
    hits = keyword_search("disk seek time track request", 1, store)
    assert len(hits) == 1
    hits = keyword_search("disk seek time track request", 10, store)
    assert [s for _, s in hits] == sorted((s for _, s in hits), reverse=True)


@pytest.mark.parametrize("q", ['"', "NEAR(", "a AND OR", "*", "seek -time", "x:y", "'; DROP TABLE chunks; --"])
def test_fts_syntax_in_question_never_raises(store, q):
    keyword_search(q, 5, store)                      # no sqlite3.OperationalError


def test_empty_or_stopword_query_and_bad_k(store):
    assert keyword_search("   ", 5, store) == [] and keyword_search("what is it", 5, store) == []
    with pytest.raises(ValueError):
        keyword_search("seek", 0, store)


def test_filters_by_unit_and_document(store):
    assert keyword_search("setuid", 5, store, SearchFilters(units=["Unit 4"])) == []
    assert len(keyword_search("setuid", 5, store, SearchFilters(units=["Unit 5"]))) == 1
    d4 = store.find_active_by_name("Unit 4_Disk.pdf").doc_id
    assert {store.get_chunks([c])[c].file_name for c, _ in keyword_search("seek C-LOOK", 5, store,
                                                                          SearchFilters(doc_ids=[d4]))} == {"Unit 4_Disk.pdf"}
    assert keyword_search("seek", 5, store, SearchFilters(doc_ids=[])) == []


def test_replaced_documents_are_not_returned(store):
    old = store.find_active_by_name("Unit 5_Protection.pdf")
    store.mark_replaced(old.doc_id)
    assert keyword_search("setuid", 5, store) == []


# ------------------------------------------------------------------ rrf_merge (written by the author)
def _require_rrf():
    try:
        rrf_merge([])
    except NotImplementedError:
        pytest.skip("rrf_merge not written yet (the author writes it; see its docstring)")


def test_rrf_single_list_keeps_order_and_formula():
    _require_rrf()
    out = rrf_merge([[7, 3, 9]], k_rrf=60)
    assert [c for c, _ in out] == [7, 3, 9]
    assert out[0][1] == pytest.approx(1 / 61) and out[2][1] == pytest.approx(1 / 63)


def test_rrf_rewards_agreement():
    _require_rrf()
    # 5 is 2nd in both lists; 1 is 1st in one list only -> 5 wins: 2/62 > 1/61
    out = dict(rrf_merge([[1, 5, 2], [3, 5, 4]]))
    assert out[5] == pytest.approx(2 / 62)
    assert max(out, key=out.get) == 5


def test_rrf_item_in_one_list_only_still_counts():
    _require_rrf()
    out = dict(rrf_merge([[1, 2], [3]]))
    assert set(out) == {1, 2, 3} and out[3] == pytest.approx(1 / 61)


def test_rrf_ties_break_by_best_rank_then_chunk_id():
    _require_rrf()
    # same score and same best rank (1/61 + 1/62 each, both ranked 1st once) -> smaller chunk_id first
    out = rrf_merge([[20, 10], [10, 20]])
    assert [c for c, _ in out] == [10, 20] and out[0][1] == pytest.approx(out[1][1])
    # with k_rrf=0 every id below scores exactly 1.0: 5 via 1/2 + 1/2, the others via 1/1;
    # 7, 8, 9 were ranked 1st somewhere (best rank 1), 5 only 2nd -> 7, 8, 9 (by id), then 5
    assert [c for c, _ in rrf_merge([[9, 5], [8, 5], [7]], k_rrf=0)] == [7, 8, 9, 5]


def test_rrf_empty_inputs_and_k():
    _require_rrf()
    assert rrf_merge([]) == [] and rrf_merge([[], []]) == []
    assert rrf_merge([[1]], k_rrf=0)[0][1] == pytest.approx(1.0)
