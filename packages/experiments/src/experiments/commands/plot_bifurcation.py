"""Generate the bifurcation diagram figure for the pre-print."""

from __future__ import annotations

import click
import numpy as np
from experiments._cache import DEFAULT_WORKDIR, load_point_cloud, sync_run
from experiments._plotting import configure_axes, docs_figure
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from rich.console import Console
from topo_archeo.persistence import compute_persistence


@docs_figure("bifurcation.pdf")
def _make_bifurcation_figure(
    a_values: list[float],
    h1_persistent: list[int],
    h1_max_lifetime: list[float],
    h0_max_lifetime: list[float],
) -> Figure:
    """Create the bifurcation diagram."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.0, 5.5), sharex=True)
    fig.subplots_adjust(hspace=0.08)

    a = np.array(a_values)

    # Top panel: H1
    ax1.bar(a, h1_persistent, width=0.035, color="C0", alpha=0.6, zorder=2)
    ax1.set_ylabel(r"$H_1$ persistent features ($> 0.5$)")
    ax1.set_ylim(-0.3, max(h1_persistent) + 1)
    ax1.axhline(0, color="gray", linewidth=0.5, zorder=1)

    ax1_right = ax1.twinx()
    ax1_right.plot(a, h1_max_lifetime, "o-", color="C1", markersize=5, linewidth=1.5, zorder=3)
    ax1_right.axhline(0.5, color="gray", linewidth=0.8, linestyle="--", zorder=1)
    ax1_right.set_ylabel(r"$H_1$ max lifetime", color="C1")
    ax1_right.set_ylim(0, 1.1)
    ax1_right.tick_params(axis="y", colors="C1")

    configure_axes(ax1)

    # Bottom panel: H0
    ax2.plot(a, h0_max_lifetime, "s-", color="C2", markersize=6, linewidth=1.5)
    ax2.set_ylabel(r"$H_0$ max lifetime ($\sigma$)")
    ax2.set_xlabel("Perturbation amplitude $A$")
    ax2.set_xlim(-0.02, 0.32)
    configure_axes(ax2)

    ax1.text(0.03, 0.92, "(a)", transform=ax1.transAxes, fontsize=10, va="top")
    ax2.text(0.03, 0.92, "(b)", transform=ax2.transAxes, fontsize=10, va="top")

    return fig


@click.command("plot-bifurcation")
@click.option("--run-ids", type=str, required=True, help="Comma-separated run IDs in order of A.")
@click.option("--a-values", type=str, default="0.0,0.05,0.1,0.15,0.2,0.25,0.3", help="Comma-separated A values.")
@click.option("--bucket", type=str, default="", help="S3 bucket name.")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
@click.option("--workdir", type=str, default=DEFAULT_WORKDIR, help="Local cache directory.")
def plot_bifurcation(run_ids: str, a_values: str, bucket: str, environment: str, workdir: str) -> None:
    """Generate the bifurcation diagram (Figure 1 in the pre-print)."""
    console = Console()

    ids = run_ids.split(",")
    a_vals = [float(x) for x in a_values.split(",")]

    h1_persistent: list[int] = []
    h1_max_lifetime: list[float] = []
    h0_max_lifetime: list[float] = []

    for run_id, a_val in zip(ids, a_vals):
        console.print(f"  A={a_val}: syncing {run_id.strip()}...")
        local_dir = sync_run(run_id.strip(), bucket, environment, workdir)
        rows, _ = load_point_cloud(local_dir)
        cloud = np.array(rows, dtype=np.float64)
        result = compute_persistence(cloud, max_dim=1)

        h1_lt = result.lifetimes(1)
        h0_lt = result.lifetimes(0)

        h1_persistent.append(result.n_persistent_features(1, 0.5))
        h1_max_lifetime.append(float(h1_lt[0]) if len(h1_lt) > 0 else 0.0)
        h0_max_lifetime.append(float(h0_lt[0]) if len(h0_lt) > 0 else 0.0)

    console.print("[bold]Generating bifurcation figure...[/bold]")
    _make_bifurcation_figure(a_vals, h1_persistent, h1_max_lifetime, h0_max_lifetime)
