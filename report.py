"""report.py -- synthesizes the plain-language report from indicator
readings. Claude only narrates already-computed findings (DEMO_MODE
default, or a real API call in live mode); it never computes or re-scores
anything. Every generated report -- Claude-authored or template -- is
run through framing_guard.assert_clean() before being returned. A
violation raises, it is never silently shown.
"""
from __future__ import annotations

from config import CLAUDE_MODEL, DEMO_MODE, INDICATOR_COUNT, SCOPE_DISCLAIMER
from framing_guard import assert_clean
from models import Dataset, IndicatorReading


class ReportError(Exception):
    pass


def _template_report(dataset: Dataset, readings: list[IndicatorReading]) -> str:
    elevated = [r for r in readings if r.elevated]
    lines = [
        f"Synthetic Content Signal Report -- {dataset.name}",
        "",
        SCOPE_DISCLAIMER,
        "",
    ]
    for r in readings:
        lines += [
            f"[{'ELEVATED' if r.elevated else 'not elevated'}] {r.label}",
            f"  Measured: {r.raw_metric}",
            f"  What this shows: {r.what_it_shows}",
            f"  What this does NOT prove: {r.what_it_does_not_prove}",
            f"  Confidence: {r.confidence}",
            f"  Source: {r.citation}",
            "",
        ]
    lines += [
        f"Summary: {len(elevated)} of {INDICATOR_COUNT} indicators show elevated readings "
        "consistent with documented templated/coordinated-content patterns.",
        f"This does NOT mean {len(elevated)}/{INDICATOR_COUNT} (or any percentage) of these "
        "accounts are bots, or that any percentage of this content is synthetic -- see each "
        "indicator's 'what this does NOT prove' line above.",
    ]
    return "\n".join(lines)


def _claude_report(dataset: Dataset, readings: list[IndicatorReading]) -> str:
    import os

    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ReportError("ANTHROPIC_API_KEY not set")

    findings_text = "\n".join(
        f"- {r.label}: {'ELEVATED' if r.elevated else 'not elevated'} -- {r.raw_metric}\n"
        f"  Shows: {r.what_it_shows}\n  Does NOT prove: {r.what_it_does_not_prove}\n  Source: {r.citation}"
        for r in readings
    )
    elevated_count = sum(1 for r in readings if r.elevated)

    prompt = f"""You are writing a plain-language report over already-computed indicator
readings for dataset "{dataset.name}". You do not compute or re-score anything -- only narrate
the findings below.

{findings_text}

STRICT RULES, NON-NEGOTIABLE:
- NEVER state or imply a percentage of accounts are bots, fake, or automated.
- NEVER state or imply a percentage of content is synthetic or AI-generated.
- NEVER use the words "definitely", "confirmed", "proves" about any account being a bot.
- Your summary sentence MUST read exactly in the form: "{elevated_count} of {INDICATOR_COUNT}
  indicators show elevated readings consistent with documented patterns."
- Immediately follow that sentence with an explicit statement that this does NOT mean any
  percentage of accounts are bots or content is synthetic.
- For each indicator, state what it shows AND what it does not prove.

Write the report now."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=1024, messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text.strip()
    except Exception as exc:  # noqa: BLE001 -- surface any SDK/network error, don't crash the CLI
        raise ReportError(f"Claude report generation failed: {exc}") from exc


def build_report(dataset: Dataset, readings: list[IndicatorReading], demo_mode: bool | None = None) -> str:
    if demo_mode is None:
        demo_mode = DEMO_MODE

    report_text = _template_report(dataset, readings) if demo_mode else _claude_report(dataset, readings)
    assert_clean(report_text)
    return report_text
