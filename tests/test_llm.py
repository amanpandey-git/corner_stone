import copy
import json

import httpx
import pytest

from cornerstone import LLMError, LLMRateLimited, LLMTimeout, LLMUnavailable
from cornerstone.llm import (AnswerCache, FakeProvider, GeminiProvider, GroqProvider, RateLimiter, get_key,
                             load_env, make_provider)

FAKE_KEY = "test-key-not-real-123"


@pytest.fixture
def lcfg(cfg, tmp_path):
    c = copy.deepcopy(cfg)
    c["paths"]["cache_dir"] = str(tmp_path / "cache")
    return c


def groq_ok(text="Paging uses frames [1]."):
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def provider(lcfg, handler, cls=GroqProvider, cache=True, sleeps=None):
    name = "groq" if cls is GroqProvider else "gemini"
    sleeps = sleeps if sleeps is not None else []
    return cls(name=name, model=lcfg["llm"][name]["model"], key=FAKE_KEY, cfg=lcfg,
               limiter=RateLimiter(1000, 10**9), cache=AnswerCache(lcfg["paths"]["cache_dir"] + "/c.sqlite") if cache else None,
               client=httpx.Client(transport=httpx.MockTransport(handler)), sleep=sleeps.append)


def test_load_env_and_missing_key(tmp_path):
    f = tmp_path / ".env"
    f.write_text("# comment\nGROQ_API_KEY=abc   # trailing\nGEMINI_API_KEY=\nX='q'\n", encoding="utf-8")
    env = load_env(f)
    assert env == {"GROQ_API_KEY": "abc", "X": "q"}
    assert get_key("groq", env) == "abc"
    with pytest.raises(LLMUnavailable, match="GEMINI_API_KEY"):
        get_key("gemini", env)
    assert load_env(tmp_path / "nope") == {}


def test_make_provider_unknown_and_no_key(lcfg):
    with pytest.raises(ValueError):
        make_provider(lcfg, "openai", env={})
    with pytest.raises(LLMUnavailable):
        make_provider(lcfg, "groq", env={})


def test_groq_request_shape_and_key_only_in_header(lcfg):
    seen = []

    def h(req: httpx.Request):
        seen.append(req)
        return groq_ok()
    p = provider(lcfg, h)
    r = p.complete("SYS", "USER", 50, 0.0)
    assert r.text == "Paging uses frames [1]." and not r.cached
    body = json.loads(seen[0].content)
    assert body["messages"][0] == {"role": "system", "content": "SYS"} and body["max_completion_tokens"] == 50
    assert seen[0].headers["authorization"] == f"Bearer {FAKE_KEY}"
    assert FAKE_KEY not in str(seen[0].url)


def test_cache_hit_makes_no_http_call(lcfg):
    calls = []

    def h(req):
        calls.append(1)
        return groq_ok()
    p = provider(lcfg, h)
    p.complete("S", "U", 10)
    r2 = p.complete("S", "U", 10)
    assert r2.cached and len(calls) == 1
    assert list(p.stream("S", "U", 10)) == ["Paging uses frames [1]."] and len(calls) == 1
    p.complete("S", "U2", 10)
    assert len(calls) == 2


def test_cache_row_never_holds_the_key(lcfg):
    p = provider(lcfg, lambda req: groq_ok())
    p.complete("S", "U", 10)
    raw = open(lcfg["paths"]["cache_dir"] + "/c.sqlite", "rb").read()
    assert FAKE_KEY.encode() not in raw


def test_retries_5xx_then_succeeds_with_backoff(lcfg):
    responses = [httpx.Response(503), httpx.Response(500), groq_ok()]
    sleeps = []
    p = provider(lcfg, lambda req: responses.pop(0), sleeps=sleeps)
    assert p.complete("S", "U", 10).text
    assert sleeps == [lcfg["llm"]["backoff_s"], lcfg["llm"]["backoff_s"] * 2]


def test_retry_cap_then_error(lcfg):
    calls = []

    def h(req):
        calls.append(1)
        return httpx.Response(503, json={"error": {"type": "service_unavailable", "message": "x"}})
    with pytest.raises(LLMError, match="503"):
        provider(lcfg, h).complete("S", "U", 10)
    assert len(calls) == 1 + lcfg["llm"]["max_retries"]


def test_429_long_retry_after_fails_at_once(lcfg):
    calls = []

    def h(req):
        calls.append(1)
        return httpx.Response(429, headers={"retry-after": "3600"}, json={"error": {"type": "rate_limit"}})
    with pytest.raises(LLMRateLimited):
        provider(lcfg, h).complete("S", "U", 10)
    assert len(calls) == 1


def test_429_short_retry_after_is_honoured(lcfg):
    responses = [httpx.Response(429, headers={"retry-after": "7"}), groq_ok()]
    sleeps = []
    provider(lcfg, lambda req: responses.pop(0), sleeps=sleeps).complete("S", "U", 10)
    assert sleeps == [7.0]


def test_auth_and_not_found_are_not_retried_and_hide_the_key(lcfg):
    for code in (401, 404):
        calls = []

        def h(req):
            calls.append(1)
            return httpx.Response(code, json={"error": {"type": "invalid_api_key", "message": f"bad key {FAKE_KEY}"}})
        with pytest.raises(LLMUnavailable) as e:
            provider(lcfg, h).complete("S", "U", 10)
        assert len(calls) == 1 and FAKE_KEY not in str(e.value)


def test_timeout_becomes_llmtimeout_after_cap(lcfg):
    calls = []

    def h(req):
        calls.append(1)
        raise httpx.ReadTimeout("slow", request=req)
    with pytest.raises(LLMTimeout):
        provider(lcfg, h).complete("S", "U", 10)
    assert len(calls) == 1 + lcfg["llm"]["max_retries"]


def test_empty_reply_is_an_error_and_not_cached(lcfg):
    p = provider(lcfg, lambda req: groq_ok(""))
    with pytest.raises(LLMError, match="empty"):
        p.complete("S", "U", 10)
    assert p.cache.get(p._cache_key("S", "U", 10, 0.0)) is None


def test_groq_streaming_parses_sse_and_caches_whole_text(lcfg):
    events = "".join(f"data: {json.dumps({'choices': [{'delta': {'content': t}}]})}\n\n" for t in ["Pag", "ing [1]."])
    p = provider(lcfg, lambda req: httpx.Response(200, text=events + "data: [DONE]\n\n"))
    assert list(p.stream("S", "U", 10)) == ["Pag", "ing [1]."]
    assert p.cache.get(p._cache_key("S", "U", 10, 0.0)) == "Paging [1]."


def test_gemini_request_shape_and_stream(lcfg):
    seen = []

    def h(req):
        seen.append(req)
        if "stream" in req.url.path:
            ev = {"candidates": [{"content": {"parts": [{"text": "A deadlock [2]."}]}}]}
            return httpx.Response(200, text=f"data: {json.dumps(ev)}\n\n")
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [
            {"text": "thinking...", "thought": True}, {"text": "A deadlock [2]."}]}}]})
    p = provider(lcfg, h, cls=GeminiProvider, cache=False)
    assert p.complete("SYS", "USER", 20).text == "A deadlock [2]."
    assert seen[0].headers["x-goog-api-key"] == FAKE_KEY and FAKE_KEY not in str(seen[0].url)
    body = json.loads(seen[0].content)
    assert body["systemInstruction"]["parts"][0]["text"] == "SYS"
    assert list(p.stream("SYS", "USER", 20)) == ["A deadlock [2]."]
    assert seen[1].url.params["alt"] == "sse"


def test_rate_limiter_waits_for_the_window():
    t = [0.0]
    slept = []

    def sleep(s):
        slept.append(s)
        t[0] += s
    rl = RateLimiter(rpm=2, tpm=1000, clock=lambda: t[0], sleep=sleep)
    assert rl.acquire(10) == 0 and rl.acquire(10) == 0
    assert rl.acquire(10) > 59 and len(slept) == 1          # third request in a minute waits
    rl2 = RateLimiter(rpm=100, tpm=100, clock=lambda: t[0], sleep=sleep)
    rl2.acquire(80)
    assert rl2.acquire(50) > 0                              # token budget, not request count


def test_fake_provider_streams_and_records():
    f = FakeProvider(["hello world [1]."], chunk=4)
    assert "".join(f.stream("s", "u", 5)) == "hello world [1]."
    assert f.complete("s", "u2", 5).text == "hello world [1]." and len(f.calls) == 2


def test_json_mode_request_fields_and_separate_cache_entry(lcfg):
    seen = []

    def h(req):
        seen.append(json.loads(req.content))
        if "generativelanguage" in str(req.url):
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})
        return groq_ok("{}")
    g = provider(lcfg, h)
    g.complete("S", "U", 10, json_mode=True)
    g.complete("S", "U", 10)                                  # plain call is a different cache entry
    assert seen[0]["response_format"] == {"type": "json_object"} and "response_format" not in seen[1]
    provider(lcfg, h, cls=GeminiProvider, cache=False).complete("S", "U", 10, json_mode=True)
    assert seen[2]["generationConfig"]["responseMimeType"] == "application/json"
