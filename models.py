"""models.py -- shared dataclasses. No logic.

Every IndicatorReading carries what_it_shows, what_it_does_not_prove, and
a citation -- structurally impossible to report a finding without also
stating its limits, mirroring the discipline P66/P70 applied to their own
indicator dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Post:
    post_id: str
    account_id: str
    text: str
    timestamp: str          # ISO 8601
    engagement_count: int    # likes + shares + replies, however the source counts it


@dataclass
class Account:
    account_id: str
    created_at: str          # ISO 8601
    follower_count: int
    posts: list[Post] = field(default_factory=list)


@dataclass
class Dataset:
    name: str
    description: str
    is_synthetic: bool
    accounts: list[Account]

    def all_posts(self) -> list[Post]:
        return [p for a in self.accounts for p in a.posts]


@dataclass
class IndicatorReading:
    indicator_id: str
    label: str
    elevated: bool
    raw_metric: str            # the actual computed number(s), stated plainly
    what_it_shows: str
    what_it_does_not_prove: str
    citation: str
    confidence: str             # e.g. "Documented pattern, moderate confidence" -- never "definitely" / "confirmed"


@dataclass
class AnalysisResult:
    dataset_name: str
    readings: list[IndicatorReading]
    elevated_count: int
    report_text: str
