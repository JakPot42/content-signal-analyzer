"""framing_guard.py -- enforces the critical framing STRUCTURALLY.

Prompting Claude nicely and hoping is not enough -- same lesson as P37's
citation_verifier and P38's force-appended LEGAL_DISCLAIMER. Every
generated report (Claude-authored or DEMO_MODE template) is scanned for
overclaiming patterns before it is ever shown. A violation is never
silently displayed; the caller must fall back to the safe deterministic
template instead.
"""
from __future__ import annotations

import re

# Each pattern targets a specific overclaiming shape this project must
# never produce, not a blunt keyword ban -- "bot" and "%" appear
# legitimately throughout indicator descriptions; what's banned is
# specifically a percentage-of-accounts-are-bots-style claim, or
# absolutist certainty language.
_VIOLATION_PATTERNS = [
    (re.compile(r"\d+(\.\d+)?%?\s*(of\s+(these|the|all|this))?\s*(accounts?|users?|posts?|content)\s+(are|is)\s+(bots?|fake|synthetic|ai[\s-]generated)", re.IGNORECASE),
     "percentage-of-accounts-are-bots claim"),
    (re.compile(r"\b(is|are)\s+(definitely|certainly|confirmed(\s+to\s+be)?)\s+(a\s+)?bots?\b", re.IGNORECASE),
     "absolutist 'definitely/confirmed bot' claim"),
    (re.compile(r"\bthis\s+(proves|confirms)\s+(that\s+)?(it|they|this|these)\s+(is|are)\s+(a\s+)?bots?\b", re.IGNORECASE),
     "'this proves/confirms bot' claim"),
    (re.compile(r"\d+%\s+of\s+(this|the)\s+(dataset|sample|content)\s+is\s+synthetic", re.IGNORECASE),
     "percentage-of-content-is-synthetic claim"),
]


def check_framing_violations(report_text: str) -> list[str]:
    """Returns a list of human-readable violation descriptions -- empty if
    the text is clean. Never raises; callers decide what to do with a
    non-empty result (reject and fall back, in this project's case)."""
    violations = []
    for pattern, description in _VIOLATION_PATTERNS:
        if pattern.search(report_text):
            violations.append(description)
    return violations


def assert_clean(report_text: str) -> None:
    """Raises ValueError if the report text violates the framing. Used as
    a hard gate before any report is returned to a caller."""
    violations = check_framing_violations(report_text)
    if violations:
        raise ValueError(
            "Generated report violates the mandatory framing discipline: " + "; ".join(violations)
        )
