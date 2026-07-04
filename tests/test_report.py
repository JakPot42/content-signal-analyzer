import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators import ALL_INDICATORS
from report import build_report
from seed_data import COORDINATED_CLUSTER, ORGANIC_BASELINE


def test_template_report_is_clean_and_uses_the_required_summary_form():
    readings = [ind(COORDINATED_CLUSTER) for ind in ALL_INDICATORS]
    report_text = build_report(COORDINATED_CLUSTER, readings, demo_mode=True)
    assert "5 of 5 indicators show elevated readings" in report_text
    assert "does NOT mean" in report_text


def test_template_report_for_clean_dataset_says_zero_elevated():
    readings = [ind(ORGANIC_BASELINE) for ind in ALL_INDICATORS]
    report_text = build_report(ORGANIC_BASELINE, readings, demo_mode=True)
    assert "0 of 5 indicators show elevated readings" in report_text


def test_report_never_states_a_bot_percentage():
    readings = [ind(COORDINATED_CLUSTER) for ind in ALL_INDICATORS]
    report_text = build_report(COORDINATED_CLUSTER, readings, demo_mode=True)
    import re
    assert not re.search(r"\d+%\s*(of\s+(these|the|all))?\s*(accounts?|users?)\s*(are|is)\s*bots?", report_text, re.IGNORECASE)
