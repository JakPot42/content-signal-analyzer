import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from framing_guard import assert_clean, check_framing_violations


def test_clean_text_has_no_violations():
    text = "3 of 5 indicators show elevated readings consistent with documented patterns."
    assert check_framing_violations(text) == []
    assert_clean(text)  # must not raise


def test_catches_percentage_of_accounts_are_bots():
    text = "Analysis shows 62% of these accounts are bots."
    violations = check_framing_violations(text)
    assert violations
    with pytest.raises(ValueError):
        assert_clean(text)


def test_catches_percentage_of_content_is_synthetic():
    text = "Roughly 40% of this dataset is synthetic."
    assert check_framing_violations(text)


def test_catches_definitely_a_bot():
    text = "This account is definitely a bot based on the evidence."
    assert check_framing_violations(text)


def test_catches_confirmed_bot():
    text = "The account is confirmed to be a bot."
    assert check_framing_violations(text)


def test_catches_this_proves_bot():
    text = "This proves that they are bots operating together."
    assert check_framing_violations(text)


def test_does_not_flag_legitimate_use_of_the_word_bot_in_citations():
    """The word 'bot' appears legitimately throughout citations and
    indicator descriptions (Botometer, 'bot detection research', etc.) --
    the guard must not blanket-ban the word itself."""
    text = "This is based on Botometer/OSoMe bot detection research and documented patterns."
    assert check_framing_violations(text) == []
