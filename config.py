"""config.py -- constants, thresholds, and mandatory framing text. No logic.

MANDATORY FRAMING (the most important discipline in this project): this
tool does NOT claim to detect bots and does NOT estimate what percentage
of content or accounts are synthetic. That claim is unverifiable at scale
from public data alone -- the same overclaiming trap as the portfolio's
rejected "predict SCOTUS outcomes" feature. Every output is scoped to
"N of 5 indicators show elevated readings consistent with documented
patterns," never "X% of these accounts are bots." See README.md.
"""
from __future__ import annotations

DEMO_MODE = True
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# The single most important string in this project. Printed on every CLI
# command and force-checked against every generated report (see
# framing_guard.py) -- not just stated once and trusted.
# ---------------------------------------------------------------------------
SCOPE_DISCLAIMER = (
    "This tool measures SPECIFIC, DOCUMENTED indicators associated with "
    "templated/coordinated content in published research. It does NOT "
    "detect bots. It does NOT estimate what percentage of accounts or "
    "content is synthetic, AI-generated, or fake -- that determination is "
    "unverifiable at scale from public data alone. Every finding below is "
    "reported as an indicator reading with an explicit confidence bound, "
    "never a bot/synthetic-content percentage. Output is always framed as "
    "\"N of 5 indicators show elevated readings,\" never as a claim about "
    "any specific account or the dataset as a whole."
)

SYNTHETIC_DATA_DISCLAIMER = (
    "The bundled demo datasets are SYNTHETIC DEMO DATA, fabricated for "
    "this demonstration -- not real accounts or real posts. Same "
    "disclosure discipline as PatientFusion (P30), BillShield AI (P38), "
    "and Agent Trust Verifier (P70). Point `analyze file` at your own "
    "real, ethically-sourced dataset (matching models.py's schema) to "
    "analyze real content; this project does not publish analysis of any "
    "real, identifiable account."
)

INDICATOR_COUNT = 5

# ---------------------------------------------------------------------------
# Indicator 1: Template repetition rate
#
# Adapted from the BM25/IDF machinery already used in P22 (civic_rag) and
# P41 (portfolio_rag) -- NOT literal BM25 itself. BM25 is an asymmetric
# ranking function (query vs. corpus), not a normalized pairwise similarity
# metric, so template-repetition detection here uses IDF-weighted cosine
# similarity: same tokenizer, same IDF weighting scheme as P22/P41's
# BM25Index, repackaged as a symmetric [0,1] pairwise score suited to
# near-duplicate detection between two specific posts.
#
# Citation: Meta's Adversarial Threat Report (Aug 2022, Mar 2023, Aug 2023)
# and Google/Mandiant's Dragonbridge analysis (Aug 2022) repeatedly cite
# "identical or near-identical content posted by multiple accounts" as a
# documented coordinated-inauthentic-behavior indicator -- same real
# sources already verified and cited in this portfolio's P68
# (dragonbridge_analyzer).
# ---------------------------------------------------------------------------
TEMPLATE_SIMILARITY_THRESHOLD = 0.75  # IDF-weighted cosine similarity -- a DIFFERENT metric than P68's 0.85 Jaccard-on-bigrams threshold, not numerically equivalent
TEMPLATE_REPETITION_RATE_ELEVATED = 0.15  # >=15% of posts have a cross-account near-duplicate above threshold
TEMPLATE_REPETITION_CITATION = (
    "Meta Adversarial Threat Report (Aug 2022, Mar 2023, Aug 2023) and "
    "Google/Mandiant Dragonbridge analysis (Aug 2022): near-identical "
    "content posted by multiple accounts is a documented coordinated-"
    "inauthentic-behavior indicator, not proof of automation or a bot."
)

# ---------------------------------------------------------------------------
# Indicator 2: Posting velocity distribution
#
# Citation: Barabasi, "The origin of bursts and heavy tails in human
# dynamics," Nature 435 (2005) -- human activity timing is documented as
# "bursty" (irregular, clustered), not uniform; Botometer/OSoMe (Indiana
# University) uses temporal regularity as one of its published feature
# categories; RTbust (arXiv:1902.04506) and "Collective behaviour of
# social bots is encoded in their temporal Twitter activity"
# (arXiv:1706.00077) both document near-uniform posting intervals and
# all-hours activity (no sleep-consistent quiet window) as documented
# automation-associated signals.
# ---------------------------------------------------------------------------
VELOCITY_MIN_POSTS_FOR_SIGNAL = 5      # below this, timing statistics are too noisy to read
VELOCITY_LOW_CV_THRESHOLD = 0.5        # coefficient of variation of inter-post intervals below this = suspiciously regular
VELOCITY_MIN_QUIET_HOURS = 5           # a human sleep-consistent quiet window is documented as several contiguous hours
VELOCITY_CITATION = (
    "Barabasi (2005), 'The origin of bursts and heavy tails in human "
    "dynamics,' Nature 435: human posting timing is documented as "
    "irregular/bursty, not uniform. Botometer/OSoMe (Indiana University) "
    "temporal-pattern features; RTbust (arXiv:1902.04506); 'Collective "
    "behaviour of social bots is encoded in their temporal Twitter "
    "activity' (arXiv:1706.00077). Near-uniform intervals or no "
    "sleep-consistent quiet window are documented automation-associated "
    "patterns, not proof any specific account is automated."
)

# ---------------------------------------------------------------------------
# Indicator 3: Cross-account coordination signal
#
# Reuses indicator 1's similarity engine + the SAME 30-minute narrow-
# window threshold already established and cited in this portfolio's P68
# (VELOCITY_TIME_WINDOW = 1800 seconds), sourced from the same Meta ATR /
# Dragonbridge coordinated-inauthentic-behavior methodology.
# ---------------------------------------------------------------------------
COORDINATION_TIME_WINDOW_SECONDS = 1800  # 30 minutes -- same threshold P68 already verified from Meta ATR/Dragonbridge methodology
COORDINATION_MIN_ACCOUNT_PAIRS = 2        # at least 2 distinct account-pairs showing the pattern
COORDINATION_CITATION = (
    "Same Meta Adversarial Threat Report / Google-Mandiant Dragonbridge "
    "coordinated-inauthentic-behavior methodology as indicator 1: "
    "networks of accounts posting near-identical content within a narrow "
    "time window (here, 30 minutes, the same threshold already verified "
    "in this portfolio's P68) is a documented coordination indicator, not "
    "proof of centralized control or automation."
)

# ---------------------------------------------------------------------------
# Indicator 4: Engagement-to-follower ratio anomaly
#
# Citation: The New York Times, "The Follower Factory" (Jan 27, 2018,
# Confessore et al.) documented purchased followers with negligible
# engagement; Cresci et al.'s fake-follower detection research uses
# friend/follower ratio and engagement metrics as classifier features.
# Thresholds below are disclosed, round-number approximations of typical
# organic engagement-rate ranges, not a precise external standard.
# ---------------------------------------------------------------------------
ENGAGEMENT_RATE_ORGANIC_MAX = 0.05   # ~5% engagement-per-follower is a commonly cited rough upper bound for organic engagement
ENGAGEMENT_RATE_HIGH_ANOMALY = 0.25  # far above organic range -- possible purchased/coordinated engagement
ENGAGEMENT_RATE_LOW_ANOMALY = 0.002  # far below organic range on a high-follower account -- possible purchased/inactive followers
MIN_FOLLOWERS_FOR_LOW_ANOMALY_CHECK = 500
ENGAGEMENT_FOLLOWER_CITATION = (
    "New York Times, 'The Follower Factory' (Jan 27, 2018): documented "
    "purchased-follower accounts with high follower counts and "
    "negligible engagement. Cresci et al. fake-follower detection "
    "research uses engagement/follower ratio as a classifier feature. "
    "Thresholds here are disclosed round-number approximations of a "
    "typical organic engagement-rate range, not a precise external "
    "standard -- an anomalous ratio is a documented pattern, not proof "
    "of purchased engagement or automation."
)

# ---------------------------------------------------------------------------
# Indicator 5: Account age vs. activity density
#
# Citation: Stanford Internet Observatory and Meta ATR takedown reports
# repeatedly document "newly created, immediately high-volume" accounts as
# a sock-puppet/burner-account pattern; "A Decade of Social Bot Detection"
# (arXiv:2007.03604) surveys account-age/activity-density as a standard
# feature category across the field.
# ---------------------------------------------------------------------------
NEW_ACCOUNT_AGE_DAYS_THRESHOLD = 30
HIGH_ACTIVITY_DENSITY_POSTS_PER_DAY = 5.0
ACCOUNT_AGE_ACTIVITY_CITATION = (
    "Stanford Internet Observatory and Meta Adversarial Threat Report "
    "takedown reports document 'newly created, immediately high-volume' "
    "accounts as a documented sock-puppet/burner-account pattern. 'A "
    "Decade of Social Bot Detection' (arXiv:2007.03604) surveys account-"
    "age/activity-density as a standard feature category. A new account "
    "posting at high density is a documented pattern, not proof of "
    "inauthenticity -- genuine new users sometimes post heavily too."
)
