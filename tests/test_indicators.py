import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import indicators
from models import Account, Dataset, Post
from seed_data import COORDINATED_CLUSTER, ORGANIC_BASELINE


def _dataset(accounts):
    return Dataset(name="test", description="test", is_synthetic=True, accounts=accounts)


def _post(pid, aid, text, ts, engagement=1):
    return Post(post_id=pid, account_id=aid, text=text, timestamp=ts, engagement_count=engagement)


# ---------------------------------------------------------------------------
# Bundled demo datasets -- regression-pins the discriminating behavior
# ---------------------------------------------------------------------------

def test_coordinated_cluster_trips_all_five():
    readings = [ind(COORDINATED_CLUSTER) for ind in indicators.ALL_INDICATORS]
    assert all(r.elevated for r in readings), [r.label for r in readings if not r.elevated]


def test_organic_baseline_trips_none():
    readings = [ind(ORGANIC_BASELINE) for ind in indicators.ALL_INDICATORS]
    assert not any(r.elevated for r in readings), [r.label for r in readings if r.elevated]


def test_every_reading_states_what_it_does_not_prove():
    """Structural check on the discipline itself -- every single reading,
    matched or not, must carry a what_it_does_not_prove statement."""
    for dataset in (COORDINATED_CLUSTER, ORGANIC_BASELINE):
        for ind in indicators.ALL_INDICATORS:
            reading = ind(dataset)
            assert reading.what_it_does_not_prove.strip() != ""
            assert reading.citation.strip() != ""


# ---------------------------------------------------------------------------
# template_repetition
# ---------------------------------------------------------------------------

def test_template_repetition_insufficient_data_for_single_post():
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10,
                            posts=[_post("p1", "a1", "hello world", "2026-01-01T00:00:00Z")])])
    reading = indicators.template_repetition(ds)
    assert reading.elevated is False
    assert "insufficient" in reading.raw_metric.lower()


def test_template_repetition_not_elevated_for_distinct_text():
    ds = _dataset([
        Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10,
                posts=[_post("p1", "a1", "completely unique text about gardening", "2026-01-01T00:00:00Z")]),
        Account(account_id="a2", created_at="2026-01-01T00:00:00Z", follower_count=10,
                posts=[_post("p2", "a2", "totally different content about cars", "2026-01-01T01:00:00Z")]),
    ])
    reading = indicators.template_repetition(ds)
    assert reading.elevated is False


# ---------------------------------------------------------------------------
# posting_velocity
# ---------------------------------------------------------------------------

def _uniform_posts(account_id, count, interval_hours=4, start_hour=0):
    start = datetime(2026, 1, 1, start_hour, tzinfo=timezone.utc)
    return [_post(f"{account_id}-p{i}", account_id, "text", (start + timedelta(hours=interval_hours * i)).isoformat()) for i in range(count)]


def test_posting_velocity_insufficient_data():
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10, posts=_uniform_posts("a1", 2))])
    reading = indicators.posting_velocity(ds)
    assert "insufficient" in reading.raw_metric.lower()


def test_posting_velocity_elevated_for_uniform_all_hours_posting():
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10, posts=_uniform_posts("a1", 12))])
    reading = indicators.posting_velocity(ds)
    assert reading.elevated is True


def test_posting_velocity_not_elevated_for_bursty_with_quiet_window():
    start = datetime(2026, 1, 1, 9, tzinfo=timezone.utc)
    times = [0, 0.2, 0.5, 3, 3.1, 6, 10, 10.5]  # hours from start, all within a 9am-11pm-style window each day
    posts = [_post(f"a1-p{i}", "a1", "text", (start + timedelta(days=int(h // 12), hours=h % 12)).isoformat()) for i, h in enumerate(times)]
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10, posts=posts)])
    reading = indicators.posting_velocity(ds)
    assert reading.elevated is False


# ---------------------------------------------------------------------------
# cross_account_coordination
# ---------------------------------------------------------------------------

def test_coordination_not_elevated_when_matching_text_is_far_apart_in_time():
    ds = _dataset([
        Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10,
                posts=[_post("p1", "a1", "Just tried NeoGlow Serum and it's AMAZING!", "2026-01-01T00:00:00Z")]),
        Account(account_id="a2", created_at="2026-01-01T00:00:00Z", follower_count=10,
                posts=[_post("p2", "a2", "Just tried NeoGlow Serum and it's AMAZING!", "2026-01-05T00:00:00Z")]),
    ])
    reading = indicators.cross_account_coordination(ds)
    assert reading.elevated is False


def test_coordination_ignores_same_account_pairs():
    ds = _dataset([
        Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10, posts=[
            _post("p1", "a1", "Just tried NeoGlow Serum and it's AMAZING!", "2026-01-01T00:00:00Z"),
            _post("p2", "a1", "Just tried NeoGlow Serum and it's AMAZING!", "2026-01-01T00:05:00Z"),
        ]),
    ])
    reading = indicators.cross_account_coordination(ds)
    assert "0 distinct" in reading.raw_metric


# ---------------------------------------------------------------------------
# engagement_follower_anomaly
# ---------------------------------------------------------------------------

def test_engagement_high_anomaly_flagged():
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=50,
                            posts=[_post("p1", "a1", "t", "2026-01-01T00:00:00Z", engagement=40)])])
    reading = indicators.engagement_follower_anomaly(ds)
    assert reading.elevated is True


def test_engagement_low_anomaly_flagged_only_above_follower_floor():
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10000,
                            posts=[_post("p1", "a1", "t", "2026-01-01T00:00:00Z", engagement=1)])])
    reading = indicators.engagement_follower_anomaly(ds)
    assert reading.elevated is True


def test_engagement_normal_range_not_elevated():
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=1000,
                            posts=[_post("p1", "a1", "t", "2026-01-01T00:00:00Z", engagement=20)])])
    reading = indicators.engagement_follower_anomaly(ds)
    assert reading.elevated is False


# ---------------------------------------------------------------------------
# account_age_activity_density
# ---------------------------------------------------------------------------

def test_new_high_density_account_flagged():
    posts = [_post(f"p{i}", "a1", "t", (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)).isoformat()) for i in range(20)]
    ds = _dataset([Account(account_id="a1", created_at="2026-01-01T00:00:00Z", follower_count=10, posts=posts)])
    reading = indicators.account_age_activity_density(ds)
    assert reading.elevated is True


def test_old_low_density_account_not_flagged():
    posts = [_post("p1", "a1", "t", "2026-01-01T00:00:00Z")]
    ds = _dataset([Account(account_id="a1", created_at="2024-01-01T00:00:00Z", follower_count=10, posts=posts)])
    reading = indicators.account_age_activity_density(ds)
    assert reading.elevated is False
