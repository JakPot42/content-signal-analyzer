"""seed_data.py -- SYNTHETIC DEMO DATA (config.SYNTHETIC_DATA_DISCLAIMER).

Two fabricated datasets, deliberately contrasting, to prove the indicators
discriminate rather than flagging everything: `coordinated_cluster` is
built to trip most indicators (near-identical templated posts, uniform
round-the-clock timing, high engagement on tiny new accounts); `organic_
baseline` is built to trip none (varied real-feeling text, human-bursty
timing with an overnight quiet window, normal engagement on older
accounts). None of this describes any real person or account.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from models import Account, Dataset, Post

_TEMPLATES = [
    "Just tried NeoGlow Serum and it's AMAZING! Everyone needs to try this NOW! #trending #musthave",
    "Just tried the NeoGlow Serum and it's AMAZING! Everyone needs to try this NOW! #trending #musthave",
    "I just tried NeoGlow Serum and it's AMAZING, everyone needs to try this NOW #trending #musthave",
    "Just tried NeoGlow Serum -- it's AMAZING! Everyone needs to try this right NOW! #trending #musthave",
    "Just tried NeoGlow Serum and it is AMAZING! Everyone really needs to try this NOW! #trending #musthave",
]

_COORDINATED_START = datetime(2026, 6, 29, 8, 0, tzinfo=timezone.utc)


def _coordinated_account(index: int) -> Account:
    account_id = f"acct-c{index + 1}"
    offset_minutes = index * 5  # accounts post within minutes of each other -- narrow coordination window
    start = _COORDINATED_START + timedelta(minutes=offset_minutes)
    posts = [
        Post(
            post_id=f"{account_id}-p{i}",
            account_id=account_id,
            # Template keyed on round `i` only (not account index): every
            # account uses the SAME near-duplicate template within a given
            # round, so the posts that land in the same narrow time window
            # (offset by minutes across accounts) are also the ones that
            # textually match -- both conditions the coordination indicator
            # checks need to co-occur, not just each happen independently.
            text=_TEMPLATES[i % len(_TEMPLATES)],
            timestamp=(start + timedelta(hours=4 * i)).isoformat(),
            engagement_count=38 + (i % 3),
        )
        for i in range(12)
    ]
    return Account(account_id=account_id, created_at=start.isoformat(), follower_count=45 + index * 3, posts=posts)


COORDINATED_CLUSTER = Dataset(
    name="coordinated_cluster",
    description="SYNTHETIC. 5 fabricated accounts posting near-identical templated content on a uniform round-the-clock schedule, created shortly before posting, with engagement far exceeding their follower counts.",
    is_synthetic=True,
    accounts=[_coordinated_account(i) for i in range(5)],
)


_ORGANIC_POSTS = {
    "acct-o1": [
        "Finally finished repainting the fence this weekend, took way longer than I thought",
        "Anyone have a good recommendation for a plumber in the north side? Kitchen sink is leaking again",
        "That new coffee place on 5th is actually really good, surprised how quiet it was on a Tuesday",
        "Watched the game last night, that overtime call was ridiculous",
        "Finally got around to reading that book everyone's been talking about, halfway through and it's solid",
        "Garden's doing better this year, tomatoes are finally coming in",
        "Long week at work, glad it's Friday",
        "Took the dog to the new park by the river, he loved it",
    ],
    "acct-o2": [
        "Spent the morning debugging a race condition that turned out to be a timezone bug the whole time",
        "Conference talk got accepted, now I have to actually write the slides",
        "Coffee machine at the office finally got fixed after three weeks",
        "Anyone else's internet been flaky today or is it just my ISP",
        "Old laptop finally died, shopping for a replacement is more exhausting than it should be",
        "Team retro went long today but we actually got some good process changes out of it",
        "Started learning to bake sourdough, first loaf was a brick but the second one was decent",
    ],
    "acct-o3": [
        "Kid's soccer game got rained out again, third week in a row",
        "Tried the new recipe for chili, needs more time next time but not bad",
        "Car's making a weird noise, taking it in tomorrow and dreading the bill",
        "Neighborhood association meeting ran two hours over, still no decision on the sidewalk repair",
        "Finally organized the garage, found tools I forgot I owned",
        "Older kid started driving lessons this week, I have never been more nervous in a passenger seat",
    ],
    "acct-o4": [
        "Museum's new exhibit is worth the trip if you're in the area this month",
        "Trying to get back into running, day two and my legs already hate me",
        "Power went out for a few hours last night, found out how many things in the house need it to work",
        "Book club picked a real doorstopper this time, wish us luck",
        "Finally beat that boss I've been stuck on for a week, felt way too good",
        "Went to the farmers market for the first time this season, peaches were incredible",
        "Spent way too long picking a paint color for the hallway, went with the first one I looked at anyway",
    ],
    "acct-o5": [
        "Whole apartment building lost water pressure this morning, landlord says it'll be fixed by tonight",
        "Finally tried that trail everyone recommends, view at the top was worth the climb",
        "Printer jammed right before a deadline, of course",
        "Started a new show, three episodes in and I'm already invested",
        "Went to visit family for the weekend, good to get away for a bit",
        "Local bakery started selling a new pastry, already my new favorite",
        "Finished a big project at work today, taking tomorrow slow",
        "Weather finally cooled off enough to open the windows again",
    ],
}

_ACCOUNT_PROFILES = {
    "acct-o1": {"created_days_before_last": 620, "follower_count": 480, "wake_hour": 7, "sleep_hour": 23},
    "acct-o2": {"created_days_before_last": 900, "follower_count": 1200, "wake_hour": 6, "sleep_hour": 22},
    "acct-o3": {"created_days_before_last": 340, "follower_count": 310, "wake_hour": 8, "sleep_hour": 22},
    "acct-o4": {"created_days_before_last": 1500, "follower_count": 2600, "wake_hour": 9, "sleep_hour": 23},
    "acct-o5": {"created_days_before_last": 210, "follower_count": 650, "wake_hour": 7, "sleep_hour": 21},
}

_ORGANIC_LATEST = datetime(2026, 6, 29, 20, 0, tzinfo=timezone.utc)


def _organic_account(account_id: str) -> Account:
    profile = _ACCOUNT_PROFILES[account_id]
    texts = _ORGANIC_POSTS[account_id]
    created_at = _ORGANIC_LATEST - timedelta(days=profile["created_days_before_last"])

    posts = []
    # Irregular, bursty spacing within each account's own waking hours -- days
    # apart varies (1, 2, 4, 1, 3...), never uniform, and every timestamp
    # falls inside [wake_hour, sleep_hour) so there's always an overnight gap.
    day_gaps = [0, 2, 5, 6, 9, 9, 13, 16]
    hour_choices = [profile["wake_hour"] + ((i * 5) % (profile["sleep_hour"] - profile["wake_hour"])) for i in range(len(texts))]
    base_day = _ORGANIC_LATEST - timedelta(days=day_gaps[len(texts) - 1] if len(texts) <= len(day_gaps) else 20)

    for i, text in enumerate(texts):
        day_offset = day_gaps[i] if i < len(day_gaps) else day_gaps[-1] + i
        ts = (base_day + timedelta(days=day_offset)).replace(hour=hour_choices[i], minute=(i * 17) % 60, second=0, microsecond=0)
        engagement = max(1, int(profile["follower_count"] * 0.02) + (i % 4) - 1)
        posts.append(Post(post_id=f"{account_id}-p{i}", account_id=account_id, text=text, timestamp=ts.isoformat(), engagement_count=engagement))

    return Account(account_id=account_id, created_at=created_at.isoformat(), follower_count=profile["follower_count"], posts=posts)


ORGANIC_BASELINE = Dataset(
    name="organic_baseline",
    description="SYNTHETIC. 5 fabricated accounts with varied real-feeling text, human-bursty posting timing with a nightly quiet window, and engagement within a normal organic range for their follower counts.",
    is_synthetic=True,
    accounts=[_organic_account(acct_id) for acct_id in _ACCOUNT_PROFILES],
)

DEMO_DATASETS: dict[str, Dataset] = {
    "coordinated_cluster": COORDINATED_CLUSTER,
    "organic_baseline": ORGANIC_BASELINE,
}
