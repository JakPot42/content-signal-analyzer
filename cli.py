"""
Synthetic Content Signal Analyzer (P69) CLI.

Measures 5 specific, documented indicators over a content sample and
reports "N of 5 indicators show elevated readings consistent with
documented patterns" -- NEVER a bot percentage or synthetic-content
percentage. config.SCOPE_DISCLAIMER prints on every command, and every
generated report is checked by framing_guard before being shown.

Every Table AND Panel uses box.ASCII2 -- Windows cp1252 terminal
compatibility, same discipline used across the rest of the portfolio.
"""
from __future__ import annotations

import json
import os
import sys

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import INDICATOR_COUNT, SCOPE_DISCLAIMER, SYNTHETIC_DATA_DISCLAIMER
from indicators import ALL_INDICATORS
from models import Account, Dataset, Post
from report import build_report
from seed_data import DEMO_DATASETS

console = Console(width=110)


def _print_scope() -> None:
    console.print(Panel(SCOPE_DISCLAIMER, box=box.ASCII2, title="[bold yellow]Scope[/bold yellow]", border_style="yellow"))


@click.group()
def cli() -> None:
    """Synthetic Content Signal Analyzer (P69) -- measures documented
    indicators with explicit confidence bounds. Never estimates a bot or
    synthetic-content percentage."""


def _analyze(dataset: Dataset):
    readings = [indicator(dataset) for indicator in ALL_INDICATORS]
    report_text = build_report(dataset, readings)
    return readings, report_text


def _print_analysis(dataset: Dataset, readings, report_text: str) -> None:
    t = Table(box=box.ASCII2, title=f"Indicator Readings -- {dataset.name}")
    t.add_column("Indicator")
    t.add_column("Reading")
    t.add_column("Measured", overflow="fold")
    for r in readings:
        style = "bold red" if r.elevated else "green"
        t.add_row(r.label, f"[{style}]{'ELEVATED' if r.elevated else 'not elevated'}[/{style}]", r.raw_metric)
    console.print(t)
    console.print(Panel(report_text, box=box.ASCII2, title="Report"))


@cli.command(name="indicators")
def list_indicators() -> None:
    """List the 5 indicators with their citations and confidence-bounds documentation."""
    _print_scope()
    from models import Dataset as _D

    empty = _D(name="_", description="", is_synthetic=True, accounts=[])
    for indicator in ALL_INDICATORS:
        reading = indicator(empty)
        console.print(Panel(
            f"[bold]{reading.label}[/bold]  ({reading.indicator_id})\n\n"
            f"What it shows: {reading.what_it_shows}\n\n"
            f"What it does NOT prove: {reading.what_it_does_not_prove}\n\n"
            f"Source: {reading.citation}",
            box=box.ASCII2,
        ))


@cli.group()
def analyze() -> None:
    """Run the 5-indicator analysis over a dataset."""


@analyze.command(name="demo")
@click.argument("dataset_key")
def analyze_demo(dataset_key: str) -> None:
    """Analyze one bundled synthetic demo dataset (coordinated_cluster or organic_baseline)."""
    _print_scope()
    console.print(Panel(SYNTHETIC_DATA_DISCLAIMER, box=box.ASCII2, border_style="yellow", title="[bold yellow]Synthetic Data[/bold yellow]"))
    dataset = DEMO_DATASETS.get(dataset_key)
    if dataset is None:
        known = ", ".join(DEMO_DATASETS)
        console.print(f"[bold red]Unknown demo dataset '{dataset_key}'.[/bold red] Known: {known}")
        return
    readings, report_text = _analyze(dataset)
    _print_analysis(dataset, readings, report_text)


@analyze.command(name="file")
@click.argument("path")
def analyze_file(path: str) -> None:
    """Analyze a user-supplied dataset (JSON file matching models.py's schema)."""
    _print_scope()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    accounts = [
        Account(
            account_id=a["account_id"], created_at=a["created_at"], follower_count=a["follower_count"],
            posts=[Post(**p) for p in a.get("posts", [])],
        )
        for a in data["accounts"]
    ]
    dataset = Dataset(name=data.get("name", path), description=data.get("description", ""), is_synthetic=data.get("is_synthetic", False), accounts=accounts)
    readings, report_text = _analyze(dataset)
    _print_analysis(dataset, readings, report_text)


@cli.command()
def demo() -> None:
    """Run both bundled demo datasets, side by side, to show the indicators discriminate."""
    _print_scope()
    console.print(Panel(SYNTHETIC_DATA_DISCLAIMER, box=box.ASCII2, border_style="yellow", title="[bold yellow]Synthetic Data[/bold yellow]"))
    t = Table(box=box.ASCII2, title="Demo Dataset Comparison")
    t.add_column("Dataset")
    t.add_column("Elevated Indicators", justify="right")
    for key, dataset in DEMO_DATASETS.items():
        readings, _ = _analyze(dataset)
        elevated = sum(1 for r in readings if r.elevated)
        style = "bold red" if elevated >= 3 else ("yellow" if elevated >= 1 else "green")
        t.add_row(key, f"[{style}]{elevated} of {INDICATOR_COUNT}[/{style}]")
    console.print(t)
    console.print("Run `py cli.py analyze demo <dataset_key>` for the full indicator breakdown and report.")


if __name__ == "__main__":
    cli()
