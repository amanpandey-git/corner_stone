"""Provider-agnostic LLM layer: Groq and Gemini over plain HTTP, plus a fake for tests (ARCHITECTURE.md 11.1).

Every call goes: cache -> rate limiter -> HTTP with a timeout -> at most llm.max_retries retries.
API keys live only in HTTP headers. They never appear in URLs, logs, cache rows or error messages.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Mapping, Protocol

import httpx

from cornerstone import LLMError, LLMRateLimited, LLMTimeout, LLMUnavailable

ROOT = Path(__file__).resolve().parents[2]
KEY_VARS = {"groq": "GROQ_API_KEY", "groq_judge": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY"}
_RETRYABLE = {429, 500, 502, 503, 504}


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    cached: bool = False
    ttft_ms: float | None = None   # time to first token (streaming only)
    total_ms: float = 0.0


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(self, system: str, user: str, max_tokens: int, temperature: float,
                 json_mode: bool = False) -> LLMResponse: ...
    def stream(self, system: str, user: str, max_tokens: int, temperature: float) -> Iterator[str]: ...
    # after stream() finishes, last_cached tells whether the text came from the cache (for honest TTFT numbers)
    last_cached: bool


# ------------------------------------------------------------------ keys
def load_env(path: Path) -> dict[str, str]:
    """Read KEY=value lines (# comments, blank values and quotes handled). Missing file -> {}."""
    out: dict[str, str] = {}
    if not Path(path).is_file():
        return out
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.split(" #", 1)[0].split("\t#", 1)[0].strip().strip('"').strip("'")
        if v:
            out[k.strip()] = v
    return out


def get_key(provider: str, env: Mapping[str, str] | None = None) -> str:
    """The provider's API key from env (default: os.environ, then .env). Raises LLMUnavailable if unset."""
    var = KEY_VARS[provider]
    if env is None:
        env = {**load_env(ROOT / ".env"), **{k: v for k, v in os.environ.items() if v}}
    key = (env.get(var) or "").strip()
    if not key:
        raise LLMUnavailable(f"{var} is not set (copy .env.example to .env and fill it in)")
    return key


# ------------------------------------------------------------------ rate limiting
class RateLimiter:
    """Sliding 60 s window over requests and (estimated) tokens. acquire() sleeps until both fit."""

    def __init__(self, rpm: int, tpm: int, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.rpm, self.tpm = rpm, tpm
        self.clock, self.sleep = clock, sleep
        self.events: deque[tuple[float, int]] = deque()   # (time, tokens)
        self.lock = threading.Lock()

    def acquire(self, tokens: int) -> float:
        """Block until a request of ~tokens fits in the window; return seconds waited."""
        tokens = min(tokens, self.tpm)   # a single request larger than the budget still goes, alone
        waited = 0.0
        with self.lock:
            while True:
                now = self.clock()
                while self.events and now - self.events[0][0] >= 60.0:
                    self.events.popleft()
                used = sum(t for _, t in self.events)
                if len(self.events) < self.rpm and used + tokens <= self.tpm:
                    self.events.append((now, tokens))
                    return waited
                wait = 60.0 - (now - self.events[0][0]) + 0.05
                self.sleep(wait)
                waited += wait


def estimate_tokens(system: str, user: str, max_tokens: int) -> int:
    """~4 characters per token for English, plus the reply budget."""
    return (len(system) + len(user)) // 4 + max_tokens


# ------------------------------------------------------------------ cache
class AnswerCache:
    """SQLite cache of successful completions, keyed by everything that determines the reply."""

    def __init__(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = Path(path)
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS llm_cache (key TEXT PRIMARY KEY, text TEXT NOT NULL, "
                      "provider TEXT, model TEXT, created REAL)")

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)   # short-lived: safe across threads (Streamlit, FastAPI)

    @staticmethod
    def key(provider: str, model: str, system: str, user: str, max_tokens: int, temperature: float,
            json_mode: bool = False) -> str:
        parts = [provider, model, system, user, max_tokens, temperature] + (["json"] if json_mode else [])
        blob = json.dumps(parts, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def get(self, key: str) -> str | None:
        c = self._conn()
        try:
            row = c.execute("SELECT text FROM llm_cache WHERE key = ?", (key,)).fetchone()
        finally:
            c.close()
        return row[0] if row else None

    def put(self, key: str, text: str, provider: str, model: str) -> None:
        if not text.strip():
            return
        c = self._conn()
        try:
            with c:
                c.execute("INSERT OR REPLACE INTO llm_cache VALUES (?, ?, ?, ?, ?)",
                          (key, text, provider, model, time.time()))
        finally:
            c.close()


# ------------------------------------------------------------------ HTTP providers
@dataclass
class _HTTPProvider:
    """Shared retry/limit/cache logic. Subclasses build the request and parse replies."""

    name: str
    model: str
    key: str = field(repr=False)
    cfg: dict
    limiter: RateLimiter
    cache: AnswerCache | None = None
    client: httpx.Client | None = None
    sleep: Callable[[float], None] = time.sleep
    last_cached: bool = False
    last_wait_s: float = 0.0      # time the last call queued in the rate limiter (not model latency)

    def __post_init__(self) -> None:
        c = self.cfg["llm"]
        self.timeout = c["timeout_s"]
        self.max_retries = c["max_retries"]
        self.backoff = c["backoff_s"]
        self.max_backoff = c["max_backoff_s"]
        if self.client is None:
            self.client = httpx.Client(timeout=httpx.Timeout(self.timeout))

    # subclass hooks
    def _request(self, system: str, user: str, max_tokens: int, temperature: float, stream: bool,
                 json_mode: bool = False) -> dict: ...
    def _parse(self, body: dict) -> str: ...
    def _parse_stream_event(self, data: str) -> str: ...

    def _cache_key(self, system, user, max_tokens, temperature, json_mode=False) -> str:
        return AnswerCache.key(self.name, self.model, system, user, max_tokens, temperature, json_mode)

    def _error(self, r: httpx.Response) -> LLMError:
        """Status code + the provider's error type only (bodies may echo request data)."""
        try:
            err = r.json()
            err = err[0] if isinstance(err, list) else err
            kind = (err.get("error") or {}).get("type") or (err.get("error") or {}).get("status") or ""
        except Exception:
            kind = ""
        msg = f"{self.name} {self.model}: HTTP {r.status_code} {kind}".strip()
        if r.status_code in (401, 403, 404):
            return LLMUnavailable(msg + (" (model not found)" if r.status_code == 404 else " (key refused)"))
        if r.status_code == 429:
            return LLMRateLimited(msg)
        return LLMError(msg)

    def _retry_wait(self, attempt: int, r: httpx.Response | None) -> float | None:
        """Seconds to wait before retry #attempt, or None to give up now."""
        if attempt > self.max_retries:
            return None
        wait = min(self.backoff * 2 ** (attempt - 1), self.max_backoff)
        if r is not None and r.status_code == 429:
            ra = r.headers.get("retry-after")
            try:
                ra = float(ra) if ra is not None else None
            except ValueError:
                ra = None
            if ra is not None:
                if ra > self.max_backoff:
                    return None          # the provider wants a long pause: fail now instead of hanging
                wait = max(wait, ra)
        return wait

    def _send(self, req: dict, stream: bool):
        """POST with capped retries. Returns the response (stream=False) or an open stream context."""
        attempt = 0
        while True:
            attempt += 1
            r = None
            try:
                if stream:
                    ctx = self.client.stream("POST", req["url"], headers=req["headers"], json=req["json"],
                                             params=req.get("params"))
                    r = ctx.__enter__()
                    if r.status_code == 200:
                        return ctx, r
                    r.read()
                    ctx.__exit__(None, None, None)
                else:
                    r = self.client.post(req["url"], headers=req["headers"], json=req["json"],
                                         params=req.get("params"))
                    if r.status_code == 200:
                        return r
                if r.status_code not in _RETRYABLE:
                    raise self._error(r)
                err: LLMError = self._error(r)
            except httpx.TimeoutException:
                err, r = LLMTimeout(f"{self.name} {self.model}: no reply within {self.timeout} s"), None
            except httpx.TransportError as e:
                err, r = LLMError(f"{self.name} {self.model}: connection failed ({type(e).__name__})"), None
            wait = self._retry_wait(attempt, r)
            if wait is None:
                raise err
            self.sleep(wait)

    def complete(self, system: str, user: str, max_tokens: int, temperature: float = 0.0,
                 json_mode: bool = False) -> LLMResponse:
        """One reply. json_mode asks the provider for a JSON object (quiz, flashcards, judge)."""
        key = self._cache_key(system, user, max_tokens, temperature, json_mode)
        if self.cache is not None and (hit := self.cache.get(key)) is not None:
            return LLMResponse(hit, self.name, self.model, cached=True)
        self.last_wait_s = self.limiter.acquire(estimate_tokens(system, user, max_tokens))
        t = time.perf_counter()
        r = self._send(self._request(system, user, max_tokens, temperature, stream=False, json_mode=json_mode),
                       stream=False)
        text = self._parse(r.json())
        if not text.strip():
            raise LLMError(f"{self.name} {self.model}: empty reply")
        if self.cache is not None:
            self.cache.put(key, text, self.name, self.model)
        return LLMResponse(text, self.name, self.model, total_ms=(time.perf_counter() - t) * 1000)

    def stream(self, system: str, user: str, max_tokens: int, temperature: float = 0.0) -> Iterator[str]:
        """Yield text deltas. A cached reply is yielded whole. Only complete replies are cached."""
        key = self._cache_key(system, user, max_tokens, temperature)
        self.last_cached, self.last_wait_s = False, 0.0
        if self.cache is not None and (hit := self.cache.get(key)) is not None:
            self.last_cached = True
            yield hit
            return
        self.last_wait_s = self.limiter.acquire(estimate_tokens(system, user, max_tokens))
        ctx, r = self._send(self._request(system, user, max_tokens, temperature, stream=True), stream=True)
        parts: list[str] = []
        try:
            for line in r.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                delta = self._parse_stream_event(data)
                if delta:
                    parts.append(delta)
                    yield delta
        except httpx.TimeoutException as e:
            raise LLMTimeout(f"{self.name} {self.model}: stream stalled for {self.timeout} s") from e
        finally:
            ctx.__exit__(None, None, None)
        text = "".join(parts)
        if not text.strip():
            raise LLMError(f"{self.name} {self.model}: empty reply")
        if self.cache is not None:
            self.cache.put(key, text, self.name, self.model)


class GroqProvider(_HTTPProvider):
    URL = "https://api.groq.com/openai/v1/chat/completions"

    def _request(self, system, user, max_tokens, temperature, stream, json_mode=False):
        body = {"model": self.model, "messages": [{"role": "system", "content": system},
                                                  {"role": "user", "content": user}],
                "max_completion_tokens": max_tokens, "temperature": temperature, "stream": stream}
        body.update(self.cfg["llm"][self.name].get("extra", {}) or {})
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        return {"url": self.URL, "headers": {"Authorization": f"Bearer {self.key}"}, "json": body}

    def _parse(self, body):
        return (body["choices"][0]["message"].get("content") or "").strip()

    def _parse_stream_event(self, data):
        ch = json.loads(data).get("choices") or [{}]
        return (ch[0].get("delta") or {}).get("content") or ""


class GeminiProvider(_HTTPProvider):
    BASE = "https://generativelanguage.googleapis.com/v1beta/models/"

    def _request(self, system, user, max_tokens, temperature, stream, json_mode=False):
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature,
                                     **(self.cfg["llm"]["gemini"].get("generation", {}) or {})}}
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"
        method = "streamGenerateContent" if stream else "generateContent"
        return {"url": f"{self.BASE}{self.model}:{method}", "headers": {"x-goog-api-key": self.key},
                "json": body, "params": {"alt": "sse"} if stream else None}

    @staticmethod
    def _text(body: dict) -> str:
        cands = body.get("candidates") or [{}]
        parts = (cands[0].get("content") or {}).get("parts") or []
        return "".join(p.get("text", "") for p in parts if not p.get("thought"))

    def _parse(self, body):
        return self._text(body).strip()

    def _parse_stream_event(self, data):
        return self._text(json.loads(data))


# ------------------------------------------------------------------ fake (tests only)
class FakeProvider:
    """Scripted provider for unit tests: never touches the network; records every call."""

    def __init__(self, replies: list[str] | Callable[[str, str], str], name: str = "fake", model: str = "fake-1",
                 chunk: int = 7) -> None:
        self.name, self.model = name, model
        self.replies, self.chunk = replies, chunk
        self.calls: list[tuple[str, str]] = []
        self.last_cached = False
        self.last_wait_s = 0.0

    def _next(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if callable(self.replies):
            return self.replies(system, user)
        return self.replies[min(len(self.calls), len(self.replies)) - 1]

    def complete(self, system, user, max_tokens, temperature=0.0, json_mode=False) -> LLMResponse:
        return LLMResponse(self._next(system, user), self.name, self.model, total_ms=0.0)

    def stream(self, system, user, max_tokens, temperature=0.0) -> Iterator[str]:
        text = self._next(system, user)
        for i in range(0, len(text), self.chunk):
            yield text[i:i + self.chunk]


# ------------------------------------------------------------------ factory
_LIMITERS: dict[str, RateLimiter] = {}


def make_provider(cfg: dict, name: str | None = None, env: Mapping[str, str] | None = None,
                  client: httpx.Client | None = None) -> LLMProvider:
    """Provider `name` (default llm.provider) with its key, the shared per-process limiter and the cache."""
    name = name or cfg["llm"]["provider"]
    classes = {"groq": GroqProvider, "groq_judge": GroqProvider, "gemini": GeminiProvider}
    if name not in classes:
        raise ValueError(f"unknown LLM provider {name!r}; choose one of {sorted(classes)}")
    p = cfg["llm"][name]
    key = get_key(name, env)
    limiter = _LIMITERS.setdefault(name, RateLimiter(p["rpm"], p["tpm"]))
    cache = AnswerCache(Path(cfg["paths"]["cache_dir"]) / "llm_cache.sqlite") if cfg["llm"]["cache"] else None
    return classes[name](name=name, model=p["model"], key=key, cfg=cfg, limiter=limiter, cache=cache, client=client)
