# content_signal_analyzer — Synthetic Content Signal Analyzer (P69)

## Scope — the framing discipline matters more than the code

"Dead Internet Theory" (most internet content is now bot/AI-generated) is
**unverifiable at scale from public data alone** — the same overclaiming
trap as this portfolio's rejected "predict SCOTUS outcomes" feature. This
tool never estimates what fraction of an account or dataset is synthetic,
and never claims to detect a bot.

Instead: it measures **5 specific, documented indicators** from published
research and reports exactly one summary shape: **"N of 5 indicators show
elevated readings consistent with documented patterns"** — never a
percentage, never a per-account verdict. `config.SCOPE_DISCLAIMER` prints
on every command, and every generated report — Claude-authored or the
deterministic `DEMO_MODE` template — is run through `framing_guard.
assert_clean()` before it is ever shown. A report that violates the
framing raises an error; it is never silently displayed. This is the
same "enforce it structurally, don't just prompt nicely and hope" lesson
as P37's citation verifier and P38's force-appended legal disclaimer.

```
py cli.py demo                                    # both demo datasets, side by side
py cli.py analyze demo coordinated_cluster         # full breakdown + report
py cli.py analyze demo organic_baseline            # the contrasting clean case
py cli.py analyze file my_dataset.json             # your own dataset (see models.py schema)
py cli.py indicators                                # the 5 indicators + citations + confidence bounds
```

---

## The 5 indicators, each with a real citation

1. **Template repetition rate** — adapted from the BM25/IDF machinery
   already used in P22 (civic_rag) and P41 (portfolio_rag). Not literal
   BM25: BM25 is an asymmetric ranking function (query vs. corpus), not a
   normalized pairwise similarity metric, so this reuses P22/P41's exact
   tokenizer and IDF-weighting formula, repackaged as symmetric,
   [0,1]-bounded IDF-weighted cosine similarity between two specific
   posts — the minimal adaptation a near-duplicate check actually needs.
   Cites Meta's Adversarial Threat Report (Aug 2022/Mar 2023/Aug 2023)
   and Google/Mandiant's Dragonbridge analysis (Aug 2022) — the same real
   sources already verified in this portfolio's P68.
2. **Posting velocity distribution** — coefficient of variation of
   inter-post intervals, plus longest sleep-consistent quiet window in a
   24-hour histogram. Cites Barabási (2005), *"The origin of bursts and
   heavy tails in human dynamics,"* Nature 435 (human activity timing is
   documented as bursty, not uniform); Botometer/OSoMe's (Indiana
   University) published temporal-pattern feature category; RTbust
   (arXiv:1902.04506); *"Collective behaviour of social bots is encoded
   in their temporal Twitter activity"* (arXiv:1706.00077).
3. **Cross-account coordination signal** — reuses indicator 1's
   similarity engine, restricted to pairs from *different* accounts
   within the same real, already-verified 30-minute window this
   portfolio's P68 established from the same Meta ATR/Dragonbridge
   methodology.
4. **Engagement-to-follower ratio anomaly** — cites the New York Times'
   *"The Follower Factory"* (Jan 27, 2018) and Cresci et al.'s
   fake-follower detection research, which use engagement/follower ratio
   as a classifier feature. Thresholds are disclosed round-number
   approximations of a typical organic range, not a precise standard.
5. **Account age vs. activity density** — cites Stanford Internet
   Observatory and Meta ATR takedown reports' documented "newly created,
   immediately high-volume account" pattern, and *"A Decade of Social Bot
   Detection"* (arXiv:2007.03604).

Every `IndicatorReading` — matched or not — carries `what_it_shows`,
`what_it_does_not_prove`, and its citation as required dataclass fields
(`models.py`), not optional commentary. `tests/test_indicators.py`
structurally checks this for every reading the two bundled demo datasets
produce.

---

## Demo data: two contrasting, clearly-labeled SYNTHETIC datasets

**No real, identifiable account is analyzed anywhere in this repository**
— a deliberate choice, not a corner cut. Running "bot signal" indicators
against real public accounts and publishing the result, even with
disclaimers, risks being read as accusing specific real people, which is
exactly the kind of overclaiming this build's framing discipline exists
to avoid (same reasoning P30/P38/P70 applied to their own synthetic data).
`analyze file` accepts any dataset matching `models.py`'s schema, so a
user can point it at their own real, ethically-sourced data if they
choose to — this project just doesn't ship one.

- **`coordinated_cluster`** — 5 fabricated accounts posting near-identical
  templated content, created within days of posting, on a perfectly
  uniform 4-hour schedule spanning all 24 hours (no sleep-consistent
  quiet window), with engagement far exceeding their tiny follower
  counts. Trips **5 of 5** indicators.
- **`organic_baseline`** — 5 fabricated accounts with varied, distinct
  text in each account's own voice, irregular bursty posting timing
  inside a real per-account waking-hours window, older accounts, and
  engagement within a normal organic range. Trips **0 of 5** indicators.

One real bug surfaced while building the coordinated-cluster demo, caught
by actually running the analyzer rather than trusting the generator code:
the first draft cycled each account's template by `(account_index + round)
% 5`, which accidentally decorrelated "same template" from "same time
window" — posts landing in the same narrow window across accounts used
*different* templates, and matching-template posts were 4 hours apart. The
cross-account coordination indicator correctly read 0 pairs as a result.
Fixed by keying the template purely on the round number, so every account
uses the same template within a given narrow window — both conditions the
indicator checks now genuinely co-occur, matching the real pattern the
citations describe.

---

## Architecture

| File | Purpose |
|---|---|
| `config.py` | `SCOPE_DISCLAIMER`, per-indicator thresholds and real citations |
| `models.py` | `Post`/`Account`/`Dataset`, and `IndicatorReading` with mandatory `what_it_does_not_prove` |
| `similarity.py` | Adapted BM25/IDF pairwise near-duplicate scoring |
| `indicators.py` | The 5 deterministic, cited indicator functions |
| `framing_guard.py` | Structural post-hoc scan rejecting any bot/synthetic-percentage claim before display |
| `report.py` | Builds the plain-language report (DEMO_MODE template or live Claude), gated by `framing_guard` |
| `seed_data.py` | The two bundled, clearly-labeled SYNTHETIC demo datasets |
| `cli.py` | Click + Rich (`box.ASCII2`) CLI |

## Test suite

36 tests, all passing (`py -m pytest tests/`):
- `test_similarity.py` — pairwise similarity correctness (identical, unrelated, near-duplicate, empty text)
- `test_indicators.py` — every indicator's trip/no-trip behavior, insufficient-data handling, and the structural "every reading states what it does not prove" check; regression-pins the bundled demo datasets at 5-of-5 and 0-of-5
- `test_framing_guard.py` — every banned pattern actually gets caught, and legitimate uses of the word "bot" (e.g. in citations) are NOT falsely flagged
- `test_report.py` — the required "N of 5" summary form, and that the report text itself never contains a bot-percentage claim
- `test_cli.py` — every command via `click.testing.CliRunner`

## Known limitations

- Thresholds (similarity cutoff, velocity CV, engagement-ratio range,
  account-age window) are disclosed, defensible approximations grounded
  in cited research, not a precise external standard — no such standard
  exists for any of these five indicators.
- `analyze file`'s schema requires per-post engagement counts and account
  creation dates, which not every public API or export makes available
  without extra requests.
- The framing guard's regex patterns target the *shapes* of overclaiming
  this project specifically must avoid; they are not a general-purpose
  filter for every way a report could overstate a finding.
