"""Generate the calibration comparison figure for the pre-print."""

from __future__ import annotations

import click
import numpy as np
from experiments._cache import DEFAULT_WORKDIR, load_results, sync_run
from experiments._plotting import configure_axes, docs_figure
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from rich.console import Console

MIGUEL_TABLE3 = {
    "Hot/warm J": 1.8,
    "Solar": 23.7,
    "Cold J": 0.0,
    "Combined": 0.0,
    "Low mass": 73.4,
    "Failed": 1.1,
}

TYPE_MAP = {
    "hot_warm_jupiter": "Hot/warm J",
    "solar": "Solar",
    "cold_jupiter": "Cold J",
    "combined": "Combined",
    "low_mass": "Low mass",
    "failed": "Failed",
}


@docs_figure("calibration.pdf")
def _make_calibration_figure(our_pcts: dict[str, float]) -> Figure:
    """Create grouped bar chart comparing our results to Miguel Table 3."""
    fig, ax = plt.subplots(figsize=(5.0, 3.5))
    fig.subplots_adjust(bottom=0.22)

    labels = list(MIGUEL_TABLE3.keys())
    miguel_vals = [MIGUEL_TABLE3[k] for k in labels]
    our_vals = [our_pcts.get(k, 0.0) for k in labels]

    x = np.arange(len(labels))
    width = 0.35

    ax.bar(x - width / 2, miguel_vals, width, label="Miguel et al. (2011)", color="#414141", alpha=0.7)
    ax.bar(x + width / 2, our_vals, width, label="This work", color="#000000", alpha=0.7)

    ax.set_ylabel("Percentage (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.legend(frameon=False, fontsize=9)
    ax.set_ylim(0, 80)
    configure_axes(ax)

    return fig


@click.command("plot-calibration")
@click.option("--run-id", type=str, required=True, help="Run ID for calibration run.")
@click.option("--bucket", type=str, default="", help="S3 bucket name.")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
@click.option("--workdir", type=str, default=DEFAULT_WORKDIR, help="Local cache directory.")
def plot_calibration(run_id: str, bucket: str, environment: str, workdir: str) -> None:
    """Generate calibration comparison bar chart (Figure 3 in the pre-print)."""
    console = Console()

    console.print(f"  Syncing {run_id}...")
    local_dir = sync_run(run_id, bucket, environment, workdir)
    results = load_results(local_dir)

    type_counts: dict[str, int] = {}
    total = len(results)
    for r in results:
        label = TYPE_MAP.get(r.system_type, r.system_type)
        type_counts[label] = type_counts.get(label, 0) + 1

    our_pcts = {k: 100.0 * v / total for k, v in type_counts.items()} if total > 0 else {}

    console.print("[bold]Generating calibration figure...[/bold]")
    _make_calibration_figure(our_pcts)
