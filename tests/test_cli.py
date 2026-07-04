import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from click.testing import CliRunner

import cli as cli_module


def test_demo_shows_both_datasets():
    result = CliRunner().invoke(cli_module.cli, ["demo"])
    assert result.exit_code == 0, result.output
    assert "coordinated_cluster" in result.output
    assert "organic_baseline" in result.output
    assert "5 of 5" in result.output
    assert "0 of 5" in result.output


def test_analyze_demo_coordinated_cluster():
    result = CliRunner().invoke(cli_module.cli, ["analyze", "demo", "coordinated_cluster"])
    assert result.exit_code == 0, result.output
    assert "ELEVATED" in result.output
    assert "SYNTHETIC DEMO DATA" in result.output


def test_analyze_demo_unknown_key_reports_clearly():
    result = CliRunner().invoke(cli_module.cli, ["analyze", "demo", "not-a-real-dataset"])
    assert result.exit_code == 0
    assert "Unknown demo dataset" in result.output


def test_indicators_command_lists_all_five_with_citations():
    result = CliRunner().invoke(cli_module.cli, ["indicators"])
    assert result.exit_code == 0, result.output
    for label in ["Template Repetition Rate", "Posting Velocity Distribution", "Cross-Account Coordination Signal",
                  "Engagement-to-Follower Ratio Anomaly", "Account Age vs. Activity Density"]:
        assert label in result.output


def test_analyze_file_with_user_supplied_dataset(tmp_path):
    data = {
        "name": "custom_test",
        "accounts": [
            {"account_id": "x1", "created_at": "2024-01-01T00:00:00Z", "follower_count": 500,
             "posts": [{"post_id": "x1-p1", "account_id": "x1", "text": "hello there", "timestamp": "2026-01-01T00:00:00Z", "engagement_count": 10}]}
        ],
    }
    path = tmp_path / "data.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = CliRunner().invoke(cli_module.cli, ["analyze", "file", str(path)])
    assert result.exit_code == 0, result.output
    assert "custom_test" in result.output


def test_scope_disclaimer_present_on_analyze():
    result = CliRunner().invoke(cli_module.cli, ["analyze", "demo", "organic_baseline"])
    assert "does NOT" in result.output
    assert "unverifiable at scale" in result.output
