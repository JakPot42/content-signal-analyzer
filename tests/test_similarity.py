import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from similarity import build_corpus, tokenize


def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Just Tried NeoGlow Serum!!") == ["just", "tried", "neoglow", "serum"]


def test_identical_text_scores_1():
    corpus = build_corpus(["the quick brown fox", "a slow green turtle"])
    assert corpus.pairwise_similarity("the quick brown fox", "the quick brown fox") == 1.0


def test_completely_different_text_scores_0():
    corpus = build_corpus(["the quick brown fox jumps", "a completely unrelated sentence here"])
    assert corpus.pairwise_similarity("the quick brown fox jumps", "a completely unrelated sentence here") == 0.0


def test_near_duplicate_text_scores_high():
    corpus = build_corpus([
        "Just tried NeoGlow Serum and it's AMAZING! Everyone needs to try this NOW!",
        "Just tried the NeoGlow Serum and it's AMAZING! Everyone needs to try this NOW!",
        "completely different unrelated filler text about gardening and rain",
    ])
    sim = corpus.pairwise_similarity(
        "Just tried NeoGlow Serum and it's AMAZING! Everyone needs to try this NOW!",
        "Just tried the NeoGlow Serum and it's AMAZING! Everyone needs to try this NOW!",
    )
    assert sim > 0.8


def test_empty_text_scores_0():
    corpus = build_corpus(["some text here", ""])
    assert corpus.pairwise_similarity("some text here", "") == 0.0
