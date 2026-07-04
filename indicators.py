"""indicators.py -- five deterministic, cited indicator functions.

Every function takes a Dataset and returns exactly one IndicatorReading.
Thresholds and citations all live in config.py. No function here ever
concludes "this account is a bot" or estimates a synthetic-content
percentage -- see models.IndicatorReading's what_it_does_not_prove field,
populated on every single reading, matched or not.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime

from config import (
    ACCOUNT_AGE_ACTIVITY_CITATION,
    COORDINATION_CITATION,
    COORDINATION_MIN_ACCOUNT_PAIRS,
    COORDINATION_TIME_WINDOW_SECONDS,
    ENGAGEMENT_FOLLOWER_CITATION,
    ENGAGEMENT_RATE_HIGH_ANOMALY,
    ENGAGEMENT_RATE_LOW_ANOMALY,
    HIGH_ACTIVITY_DENSITY_POSTS_PER_DAY,
    MIN_FOLLOWERS_FOR_LOW_ANOMALY_CHECK,
    NEW_ACCOUNT_AGE_DAYS_THRESHOLD,
    TEMPLATE_REPETITION_CITATION,
    TEMPLATE_REPETITION_RATE_ELEVATED,
    TEMPLATE_SIMILARITY_THRESHOLD,
    VELOCITY_CITATION,
    VELOCITY_LOW_CV_THRESHOLD,
    VELOCITY_MIN_POSTS_FOR_SIGNAL,
    VELOCITY_MIN_QUIET_HOURS,
)
from models import Dataset, IndicatorReading
from similarity import build_corpus


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def template_repetition(dataset: Dataset) -> IndicatorReading:
    posts = dataset.all_posts()
    if len(posts) < 2:
        return IndicatorReading(
            indicator_id="template_repetition", label="Template Repetition Rate",
            elevated=False, raw_metric="fewer than 2 posts -- insufficient data",
            what_it_shows="Whether posts from different accounts are near-duplicates of each other.",
            what_it_does_not_prove="That any specific account is automated or that content is AI-generated.",
            citation=TEMPLATE_REPETITION_CITATION, confidence="Insufficient data to assess.",
        )

    corpus = build_corpus([p.text for p in posts])
    near_dup_count = 0
    for i, post in enumerate(posts):
        best = 0.0
        for j, other in enumerate(posts):
            if i == j or other.account_id == post.account_id:
                continue
            sim = corpus.pairwise_similarity(post.text, other.text)
            best = max(best, sim)
        if best >= TEMPLATE_SIMILARITY_THRESHOLD:
            near_dup_count += 1

    rate = near_dup_count / len(posts)
    elevated = rate >= TEMPLATE_REPETITION_RATE_ELEVATED
    return IndicatorReading(
        indicator_id="template_repetition", label="Template Repetition Rate",
        elevated=elevated,
        raw_metric=f"{near_dup_count}/{len(posts)} posts ({rate:.1%}) have a cross-account near-duplicate (IDF-cosine >= {TEMPLATE_SIMILARITY_THRESHOLD})",
        what_it_shows="The fraction of posts that closely textually match a post from a DIFFERENT account.",
        what_it_does_not_prove=(
            "That the matching accounts are automated, coordinated, or that any specific post is "
            "AI-generated -- shared talking points, retweeted/quoted text, or organic meme repetition "
            "can also produce near-duplicate content."
        ),
        citation=TEMPLATE_REPETITION_CITATION,
        confidence="Documented pattern, moderate confidence." if elevated else "No elevated signal.",
    )


def posting_velocity(dataset: Dataset) -> IndicatorReading:
    assessable = [a for a in dataset.accounts if len(a.posts) >= VELOCITY_MIN_POSTS_FOR_SIGNAL]
    if not assessable:
        return IndicatorReading(
            indicator_id="posting_velocity", label="Posting Velocity Distribution",
            elevated=False, raw_metric=f"no accounts with >= {VELOCITY_MIN_POSTS_FOR_SIGNAL} posts -- insufficient data",
            what_it_shows="Whether an account's posting timing is regular/uniform versus bursty, and whether it shows a sleep-consistent quiet window.",
            what_it_does_not_prove="That any specific account is automated.",
            citation=VELOCITY_CITATION, confidence="Insufficient data to assess.",
        )

    flagged = 0
    for account in assessable:
        times = sorted(_parse(p.timestamp) for p in account.posts)
        intervals = [(times[i + 1] - times[i]).total_seconds() for i in range(len(times) - 1)]
        mean_interval = statistics.mean(intervals) if intervals else 0.0
        cv = (statistics.pstdev(intervals) / mean_interval) if mean_interval else 0.0

        hour_counts = [0] * 24
        for t in times:
            hour_counts[t.hour] += 1
        longest_quiet = _longest_circular_zero_run(hour_counts)

        if cv < VELOCITY_LOW_CV_THRESHOLD or longest_quiet < VELOCITY_MIN_QUIET_HOURS:
            flagged += 1

    fraction = flagged / len(assessable)
    elevated = fraction >= 0.5
    return IndicatorReading(
        indicator_id="posting_velocity", label="Posting Velocity Distribution",
        elevated=elevated,
        raw_metric=f"{flagged}/{len(assessable)} assessable accounts ({fraction:.1%}) show near-uniform intervals or no sleep-consistent quiet window",
        what_it_shows="Whether posting timing is documented-bursty (human-consistent) or near-uniform/all-hours (automation-associated).",
        what_it_does_not_prove="That any specific account is automated -- shift work, multiple time zones, or scheduled posting tools used by real people can also produce this pattern.",
        citation=VELOCITY_CITATION,
        confidence="Documented pattern, moderate confidence." if elevated else "No elevated signal.",
    )


def _longest_circular_zero_run(hour_counts: list[int]) -> int:
    """Longest run of consecutive zero-post hours, wrapping around midnight."""
    if all(c == 0 for c in hour_counts):
        return 24
    doubled = hour_counts + hour_counts
    longest = current = 0
    for c in doubled:
        current = current + 1 if c == 0 else 0
        longest = max(longest, current)
    return min(longest, 24)


def cross_account_coordination(dataset: Dataset) -> IndicatorReading:
    posts = dataset.all_posts()
    if len(posts) < 2:
        return IndicatorReading(
            indicator_id="cross_account_coordination", label="Cross-Account Coordination Signal",
            elevated=False, raw_metric="fewer than 2 posts -- insufficient data",
            what_it_shows="Whether different accounts post near-duplicate content within a narrow time window.",
            what_it_does_not_prove="That any specific accounts are centrally controlled or automated.",
            citation=COORDINATION_CITATION, confidence="Insufficient data to assess.",
        )

    corpus = build_corpus([p.text for p in posts])
    coordinated_pairs: set[tuple[str, str]] = set()
    for i, post_a in enumerate(posts):
        time_a = _parse(post_a.timestamp)
        for post_b in posts[i + 1:]:
            if post_b.account_id == post_a.account_id:
                continue
            time_b = _parse(post_b.timestamp)
            if abs((time_b - time_a).total_seconds()) > COORDINATION_TIME_WINDOW_SECONDS:
                continue
            if corpus.pairwise_similarity(post_a.text, post_b.text) >= TEMPLATE_SIMILARITY_THRESHOLD:
                coordinated_pairs.add(tuple(sorted((post_a.account_id, post_b.account_id))))

    elevated = len(coordinated_pairs) >= COORDINATION_MIN_ACCOUNT_PAIRS
    window_minutes = COORDINATION_TIME_WINDOW_SECONDS // 60
    return IndicatorReading(
        indicator_id="cross_account_coordination", label="Cross-Account Coordination Signal",
        elevated=elevated,
        raw_metric=f"{len(coordinated_pairs)} distinct account-pair(s) posted near-duplicate content within {window_minutes} minutes of each other",
        what_it_shows="Whether near-duplicate content appears across different accounts within a narrow time window, beyond what indicator 1 alone shows.",
        what_it_does_not_prove="That the involved accounts are centrally controlled, automated, or affiliated -- shared breaking-news phrasing or a viral quote can also produce this pattern.",
        citation=COORDINATION_CITATION,
        confidence="Documented pattern, moderate confidence." if elevated else "No elevated signal.",
    )


def engagement_follower_anomaly(dataset: Dataset) -> IndicatorReading:
    accounts = [a for a in dataset.accounts if a.posts]
    if not accounts:
        return IndicatorReading(
            indicator_id="engagement_follower_anomaly", label="Engagement-to-Follower Ratio Anomaly",
            elevated=False, raw_metric="no accounts with posts -- insufficient data",
            what_it_shows="Whether engagement per post is anomalously high or low relative to follower count.",
            what_it_does_not_prove="That any specific account purchased followers or engagement.",
            citation=ENGAGEMENT_FOLLOWER_CITATION, confidence="Insufficient data to assess.",
        )

    flagged = 0
    for account in accounts:
        avg_engagement = statistics.mean(p.engagement_count for p in account.posts)
        rate = avg_engagement / max(account.follower_count, 1)
        high_anomaly = rate >= ENGAGEMENT_RATE_HIGH_ANOMALY
        low_anomaly = account.follower_count >= MIN_FOLLOWERS_FOR_LOW_ANOMALY_CHECK and rate <= ENGAGEMENT_RATE_LOW_ANOMALY
        if high_anomaly or low_anomaly:
            flagged += 1

    fraction = flagged / len(accounts)
    elevated = fraction >= 0.3
    return IndicatorReading(
        indicator_id="engagement_follower_anomaly", label="Engagement-to-Follower Ratio Anomaly",
        elevated=elevated,
        raw_metric=f"{flagged}/{len(accounts)} accounts ({fraction:.1%}) show an engagement/follower ratio outside the disclosed organic range",
        what_it_shows="Whether engagement-per-post relative to follower count is far above or far below a disclosed rough organic range.",
        what_it_does_not_prove="That any specific account purchased followers or engagement -- a small, highly-engaged real community or a large, dormant real audience can also produce this pattern.",
        citation=ENGAGEMENT_FOLLOWER_CITATION,
        confidence="Documented pattern, moderate confidence." if elevated else "No elevated signal.",
    )


def account_age_activity_density(dataset: Dataset) -> IndicatorReading:
    accounts = [a for a in dataset.accounts if a.posts]
    if not accounts:
        return IndicatorReading(
            indicator_id="account_age_activity_density", label="Account Age vs. Activity Density",
            elevated=False, raw_metric="no accounts with posts -- insufficient data",
            what_it_shows="Whether a new account posts at unusually high density immediately after creation.",
            what_it_does_not_prove="That any specific new, active account is inauthentic.",
            citation=ACCOUNT_AGE_ACTIVITY_CITATION, confidence="Insufficient data to assess.",
        )

    latest_post_time = max(_parse(p.timestamp) for a in accounts for p in a.posts)
    flagged = 0
    for account in accounts:
        age_days = max((latest_post_time - _parse(account.created_at)).days, 0)
        density = len(account.posts) / max(age_days, 1)
        if age_days < NEW_ACCOUNT_AGE_DAYS_THRESHOLD and density >= HIGH_ACTIVITY_DENSITY_POSTS_PER_DAY:
            flagged += 1

    fraction = flagged / len(accounts)
    elevated = fraction >= 0.3
    return IndicatorReading(
        indicator_id="account_age_activity_density", label="Account Age vs. Activity Density",
        elevated=elevated,
        raw_metric=f"{flagged}/{len(accounts)} accounts ({fraction:.1%}) are under {NEW_ACCOUNT_AGE_DAYS_THRESHOLD} days old with >= {HIGH_ACTIVITY_DENSITY_POSTS_PER_DAY} posts/day",
        what_it_shows="Whether new accounts (relative to the dataset's observation window) post at unusually high density.",
        what_it_does_not_prove="That any specific new, active account is inauthentic -- genuine new users sometimes post heavily too.",
        citation=ACCOUNT_AGE_ACTIVITY_CITATION,
        confidence="Documented pattern, moderate confidence." if elevated else "No elevated signal.",
    )


ALL_INDICATORS = [
    template_repetition,
    posting_velocity,
    cross_account_coordination,
    engagement_follower_anomaly,
    account_age_activity_density,
]
