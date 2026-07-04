"""similarity.py -- pairwise near-duplicate scoring, adapted from the
BM25/IDF machinery in P22 (civic_rag) and P41 (portfolio_rag).

Not literal BM25: BM25 is an asymmetric ranking function (score a query
against a corpus), not a normalized pairwise similarity metric between two
specific documents. Template-repetition and cross-account-coordination
detection need the latter, so this module reuses P22/P41's exact
tokenizer and IDF-weighting formula, then packages it as symmetric,
[0,1]-bounded IDF-weighted cosine similarity between two texts --
the minimal adaptation needed, not a different technique.
"""
from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]*\b")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class IDFCorpus:
    """Same IDF formula as P22/P41's BM25Index: log((N - df + 0.5)/(df + 0.5) + 1)."""

    def __init__(self, texts: list[str]):
        self._tokenized = [tokenize(t) for t in texts]
        n = len(texts)
        df: Counter = Counter()
        for tokens in self._tokenized:
            for term in set(tokens):
                df[term] += 1
        self.idf: dict[str, float] = {
            term: math.log((n - freq + 0.5) / (freq + 0.5) + 1) for term, freq in df.items()
        }

    def _weighted_vector(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        return {term: count * self.idf.get(term, 0.0) for term, count in tf.items()}

    def pairwise_similarity(self, text_a: str, text_b: str) -> float:
        """IDF-weighted cosine similarity between two texts, using this
        corpus's IDF weights. Returns 0.0 if either text has no tokens
        with nonzero weight."""
        vec_a = self._weighted_vector(tokenize(text_a))
        vec_b = self._weighted_vector(tokenize(text_b))
        if not vec_a or not vec_b:
            return 0.0

        shared_terms = set(vec_a) & set(vec_b)
        dot = sum(vec_a[t] * vec_b[t] for t in shared_terms)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)


def build_corpus(texts: list[str]) -> IDFCorpus:
    return IDFCorpus(texts)
