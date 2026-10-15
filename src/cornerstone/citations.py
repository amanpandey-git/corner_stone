"""Citation parsing and checking for grounded answers (ARCHITECTURE.md 11.3).

An answer cites its sources as [n], [n, m], [n][m] or [n-m]. parse_citations() splits the answer into
sentences and finds which sources each sentence cites, which factual sentences cite nothing, and which
numbers point at sources that do not exist. check_citations() asks a judge model whether each cited
source really supports its sentence.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

NOT_IN_NOTES_TOKEN = "NOT_IN_NOTES"
MAX_RANGE = 20   # [1-500] is a typo or a hallucination, not 500 citations

# one reference group: [3] or [1, 2] or [2-4] (also an en dash)
REF = re.compile(r"\[\s*\d+(?:\s*[,\-–]\s*\d+)*\s*\]")
# a sentence ends at . ! or ? that is followed by whitespace or the end of the line; reference
# groups written right after the full stop ("... frames. [1]") still belong to that sentence
END = re.compile(r"[.!?](?:\s*" + REF.pattern + r")*(?=\s|$)")
BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


@dataclass
class Citation:
    sentence: str        # the sentence without its reference markers
    refs: list[int]      # valid source numbers, in order of first appearance, no repeats


def _numbers(group: str) -> list[int]:
    """'[1, 3-5]' -> [1, 3, 4, 5]. A range that runs backwards or is huge yields its two ends only."""
    out: list[int] = []
    for part in group.strip("[] ").split(","):
        part = part.strip().replace("–", "-")
        if "-" in part:
            a, b = (int(x) for x in part.split("-")[:2])
            out += list(range(a, b + 1)) if 0 <= b - a <= MAX_RANGE else [a, b]
        elif part:
            out.append(int(part))
    return out


def split_sentences(text: str) -> list[str]:
    """Lines first (bullets and headings are their own units), then sentence ends inside each line."""
    out: list[str] = []
    for line in text.splitlines():
        pos = 0
        for m in END.finditer(line):
            out.append(line[pos:m.end()].strip())
            pos = m.end()
        out.append(line[pos:].strip())
    return [s for s in out if s]


def _is_factual(sentence: str) -> bool:
    """Headings, labels and the abstention token make no claim, so they need no citation."""
    s = BULLET.sub("", sentence).strip().strip("*_").strip()
    if not s or s == NOT_IN_NOTES_TOKEN or sentence.lstrip().startswith("#"):
        return False
    if s.endswith(":"):
        return False
    return len(s.split()) >= 4   # "Conclusion", "Key points" are labels, not claims


def parse_citations(text: str, n_sources: int) -> tuple[list[Citation], list[str], list[int]]:
    """Return (citations, uncited factual sentences, invalid reference numbers).

    A sentence goes to ``citations`` if it has at least one reference to a source 1..n_sources.
    A factual sentence with no valid reference goes to the uncited list. Numbers outside
    1..n_sources are collected (sorted, unique) as invalid; they never count as citations.
    """
    citations: list[Citation] = []
    uncited: list[str] = []
    invalid: set[int] = set()
    for sentence in split_sentences(text):
        refs: list[int] = []
        for group in REF.findall(sentence):
            for n in _numbers(group):
                if 1 <= n <= n_sources:
                    if n not in refs:
                        refs.append(n)
                else:
                    invalid.add(n)
        bare = " ".join(REF.sub(" ", sentence).split())
        bare = re.sub(r"\s+([.!?,;:])", r"\1", bare)
        if refs:
            citations.append(Citation(bare, refs))
        elif _is_factual(sentence):
            uncited.append(bare)
    return citations, uncited, sorted(invalid)


def strip_invalid_refs(text: str, n_sources: int) -> str:
    """Rewrite every reference group keeping only valid numbers; drop groups left empty."""
    def fix(m: re.Match) -> str:
        keep: list[int] = []
        for n in _numbers(m.group(0)):
            if 1 <= n <= n_sources and n not in keep:
                keep.append(n)
        return "[" + ", ".join(map(str, keep)) + "]" if keep else ""

    out = REF.sub(fix, text)
    return re.sub(r"[ \t]+([.!?,;:])", r"\1", re.sub(r"[ \t]{2,}", " ", out))


JUDGE_SYSTEM = (
    "You check citations in a student's study answer. For each numbered claim you get the sentence and the "
    "text of the slides it cites. A claim is SUPPORTED only if the cited slide text states it or directly "
    "implies it; general knowledge does not count. Reply with JSON only: "
    '{"unsupported": [claim numbers that are not supported]}. Use an empty list if all are supported.')


def build_judge_prompt(citations: list[Citation], source_texts: dict[int, str]) -> str:
    blocks = []
    for i, c in enumerate(citations, 1):
        cited = "\n".join(f"  [{n}] {' '.join(source_texts.get(n, '').split())}" for n in c.refs)
        blocks.append(f"Claim {i}: {c.sentence}\nCited slides:\n{cited}")
    return "\n\n".join(blocks)


def parse_judge_reply(reply: str, n_claims: int) -> list[int] | None:
    """The 0-based indexes of unsupported claims, or None if the reply is not the expected JSON."""
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        bad = data["unsupported"]
        if not isinstance(bad, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in bad):
            return None
    except (ValueError, KeyError, TypeError):
        return None
    return sorted({x - 1 for x in bad if 1 <= x <= n_claims})


def check_citations(citations: list[Citation], source_texts: dict[int, str], judge, cfg: dict) -> list[int] | None:
    """Ask the judge which citations are unsupported. None = could not be checked (never "all fine")."""
    if not citations:
        return []
    user = build_judge_prompt(citations, source_texts)
    max_tokens = cfg["answer"]["judge_max_tokens"]
    for attempt in range(2):   # one retry on malformed JSON, then give up honestly
        reply = judge.complete(JUDGE_SYSTEM + (" Reply with the JSON object only." if attempt else ""),
                               user, max_tokens, 0.0).text
        result = parse_judge_reply(reply, len(citations))
        if result is not None:
            return result
    return None
