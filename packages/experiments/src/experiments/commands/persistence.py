"""Compute persistent homology on simulation results."""

from __future__ import annotations

import click
import numpy as np
from experiments._cache import DEFAULT_WORKDIR, load_manifest, load_point_cloud, sync_run
from experiments.commands.collect import _print_manifest
from rich.console import Console
from rich.table import Table
from topo_archeo.persistence import compute_persistence


@click.command()
@click.option("--run-id", type=str, required=True, help="Run ID to analyze.")
@click.option("--bucket", type=str, default="", help="S3 bucket name.")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
@click.option("--max-dim", type=int, default=1, help="Maximum homology dimension.")
@click.option("--threshold", type=float, default=0.5, help="Persistence threshold for counting features.")
@click.option("--workdir", type=str, default=DEFAULT_WORKDIR, help="Local cache directory.")
def persistence(run_id: str, bucket: str, environment: str, max_dim: int, threshold: float, workdir: str) -> None:
    """Compute persistent homology on simulation results."""
    console = Console()

    console.print(f"[bold]Syncing results for {run_id}...[/bold]")
    local_dir = sync_run(run_id, bucket, environment, workdir)

    # Load and display manifest
    manifest = load_manifest(local_dir)
    if manifest:
        _print_manifest(console, manifest)

    rows, _system_types = load_point_cloud(local_dir)
    point_cloud = np.array(rows, dtype=np.float64)

    if point_cloud.shape[0] == 0:
        console.print("[red]No data found.[/red]")
        return

    n_systems = point_cloud.shape[0]
    console.print(f"[bold]Point cloud: {n_systems} systems x {point_cloud.shape[1]} features[/bold]")

    console.print(f"[bold]Computing Vietoris-Rips persistence (max_dim={max_dim})...[/bold]")
    result = compute_persistence(point_cloud, max_dim=max_dim)

    # Summary table
    summary = Table(title="Persistence Summary")
    summary.add_column("Dimension", style="cyan")
    summary.add_column("Total features", justify="right")
    summary.add_column("Finite features", justify="right")
    summary.add_column(f"Persistent (lifetime > {threshold})", justify="right", style="green")
    summary.add_column("Max lifetime", justify="right", style="yellow")

    for dim in range(max_dim + 1):
        dgm = result.diagrams[dim]
        finite_mask = np.isfinite(dgm[:, 1])
        n_total = len(dgm)
        n_finite = int(np.sum(finite_mask))
        lt = result.lifetimes(dim)
        n_persistent = result.n_persistent_features(dim, threshold)
        max_lt = float(lt[0]) if len(lt) > 0 else 0.0
        summary.add_row(
            f"H{dim}",
            str(n_total),
            str(n_finite),
            str(n_persistent),
            f"{max_lt:.3f}",
        )

    console.print(summary)

    # H0 interpretation
    h0_lifetimes = result.lifetimes(0)
    if len(h0_lifetimes) > 0:
        console.print("\n[bold]H0 (connected components):[/bold]")
        console.print(f"  Top 10 lifetimes: {', '.join(f'{lt:.3f}' for lt in h0_lifetimes[:10])}")
        n_clusters = result.n_persistent_features(0, threshold) + 1
        console.print(f"  Estimated clusters (threshold={threshold}): [bold green]{n_clusters}[/bold green]")

    # H1 interpretation
    if max_dim >= 1:
        h1_lifetimes = result.lifetimes(1)
        console.print("\n[bold]H1 (loops / degeneracies):[/bold]")
        if len(h1_lifetimes) > 0:
            console.print(f"  Top 10 lifetimes: {', '.join(f'{lt:.3f}' for lt in h1_lifetimes[:10])}")
            n_loops = result.n_persistent_features(1, threshold)
            console.print(f"  Significant loops (threshold={threshold}): [bold green]{n_loops}[/bold green]")
        else:
            console.print("  No H1 features detected.")
