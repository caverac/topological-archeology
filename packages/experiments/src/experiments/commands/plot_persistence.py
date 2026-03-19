"""Generate persistence diagram figures for the pre-print."""

from __future__ import annotations

import click
import numpy as np
from experiments._cache import DEFAULT_WORKDIR, load_point_cloud, sync_run
from experiments._plotting import configure_axes, docs_figure
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich.console import Console
from topo_archeo.persistence import compute_persistence


def _plot_diagram(ax: Axes, dgm: np.ndarray, dim: int, color: str) -> None:
    """Plot a single persistence diagram (birth-death scatter with diagonal)."""
    finite = dgm[np.isfinite(dgm[:, 1])]
    infinite = dgm[~np.isfinite(dgm[:, 1])]

    # Compute axis range from all birth/death values
    all_vals = []
    if len(finite) > 0:
        all_vals.extend(finite[:, 0].tolist())
        all_vals.extend(finite[:, 1].tolist())
    if len(infinite) > 0:
        all_vals.extend(infinite[:, 0].tolist())

    lo = min(all_vals) if all_vals else 0.0
    hi = max(all_vals) if all_vals else 1.0
    margin = (hi - lo) * 0.05
    lo -= margin
    hi += margin

    # Diagonal line (draw first so scatter is on top)
    ax.plot([lo, hi], [lo, hi], "k--", linewidth=0.5, alpha=0.3, zorder=1)

    if len(finite) > 0:
        ax.scatter(finite[:, 0], finite[:, 1], s=12, alpha=0.5, color=color, edgecolors="none", zorder=2)

    if len(infinite) > 0:
        y_inf = hi
        ax.scatter(infinite[:, 0], [y_inf] * len(infinite), s=30, marker="^", color=color, edgecolors="none", zorder=3)

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi * 1.05)
    ax.set_xlabel("Birth")
    ax.set_ylabel("Death")
    ax.set_title(f"$H_{dim}$", fontsize=11)
    ax.set_aspect("equal")


@docs_figure("persistence-diagrams.pdf")
def _make_persistence_figure(
    cloud_smooth: np.ndarray,
    cloud_trans: np.ndarray,
    label_smooth: str,
    label_trans: str,
) -> Figure:
    """Create side-by-side persistence diagrams for smooth vs transitional."""
    fig, axes = plt.subplots(2, 2, figsize=(6.5, 6.0))
    fig.subplots_adjust(hspace=0.35, wspace=0.35)

    result_s = compute_persistence(cloud_smooth, max_dim=1)
    result_t = compute_persistence(cloud_trans, max_dim=1)

    _plot_diagram(axes[0, 0], result_s.h0, 0, "C0")
    _plot_diagram(axes[0, 1], result_s.h1, 1, "C1")
    _plot_diagram(axes[1, 0], result_t.h0, 0, "C0")
    _plot_diagram(axes[1, 1], result_t.h1, 1, "C1")

    for ax in axes.ravel():
        configure_axes(ax)

    axes[0, 0].set_ylabel(f"{label_smooth}\nDeath")
    axes[1, 0].set_ylabel(f"{label_trans}\nDeath")

    n_h1_s = result_s.n_persistent_features(1, 0.5)
    n_h1_t = result_t.n_persistent_features(1, 0.5)
    axes[0, 1].text(0.95, 0.05, f"$\\beta_1 = {n_h1_s}$", transform=axes[0, 1].transAxes, ha="right", fontsize=10)
    axes[1, 1].text(0.95, 0.05, f"$\\beta_1 = {n_h1_t}$", transform=axes[1, 1].transAxes, ha="right", fontsize=10)

    return fig


@click.command("plot-persistence")
@click.option("--run-smooth", type=str, required=True, help="Run ID for smooth disk (A=0).")
@click.option("--run-trans", type=str, required=True, help="Run ID for transitional disk (A=0.3).")
@click.option("--bucket", type=str, default="", help="S3 bucket name.")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
@click.option("--workdir", type=str, default=DEFAULT_WORKDIR, help="Local cache directory.")
def plot_persistence(run_smooth: str, run_trans: str, bucket: str, environment: str, workdir: str) -> None:
    """Generate persistence diagram comparison (Figure 2 in the pre-print)."""
    console = Console()

    console.print(f"  Syncing smooth: {run_smooth}...")
    local_s = sync_run(run_smooth, bucket, environment, workdir)
    rows_s, _ = load_point_cloud(local_s)

    console.print(f"  Syncing transitional: {run_trans}...")
    local_t = sync_run(run_trans, bucket, environment, workdir)
    rows_t, _ = load_point_cloud(local_t)

    console.print("[bold]Generating persistence diagram figure...[/bold]")
    _make_persistence_figure(
        np.array(rows_s, dtype=np.float64),
        np.array(rows_t, dtype=np.float64),
        "$A = 0$",
        "$A = 0.3$",
    )
