"""Collect simulation results from S3 and display summary."""

from __future__ import annotations

from collections import Counter

import click
from disk_evolution.classify import SystemType
from experiments._cache import DEFAULT_WORKDIR, load_manifest, load_results, sync_run
from experiments._models import RunManifest
from rich.console import Console
from rich.table import Table

SYSTEM_TYPE_LABELS: dict[str, str] = {
    SystemType.HOT_WARM_JUPITER.value: "Hot and warm Jupiters",
    SystemType.SOLAR.value: "Solar systems",
    SystemType.COLD_JUPITER.value: "Cold Jupiter",
    SystemType.COMBINED.value: "Combined systems",
    SystemType.LOW_MASS.value: "Low mass planet systems",
    SystemType.FAILED.value: "Failed planetary systems",
}


def _print_manifest(console: Console, manifest: RunManifest) -> None:
    """Print run metadata from the manifest.

    Parameters
    ----------
    console : Console
        Rich console.
    manifest : RunManifest
        Manifest contents.
    """
    console.print("[bold]Run metadata:[/bold]")
    console.print(f"  created_at: {manifest.created_at or 'unknown'}")
    console.print(f"  n_systems:  {manifest.n_systems or 'unknown'}")
    console.print(f"  seed:       {manifest.seed or 'unknown'}")
    console.print(f"  gamma:      {manifest.config.gamma}")
    console.print(f"  c_mig_i:    {manifest.config.c_mig_i}")
    console.print(f"  A:          {manifest.config.perturbation_amplitude}")
    console.print()


@click.command()
@click.option("--run-id", type=str, required=True, help="Run ID to collect results for.")
@click.option("--bucket", type=str, default="", help="S3 bucket name (auto-discovered if empty).")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
@click.option("--workdir", type=str, default=DEFAULT_WORKDIR, help="Local cache directory.")
def collect(run_id: str, bucket: str, environment: str, workdir: str) -> None:
    """Collect simulation results from S3 and display classification table."""
    console = Console()

    console.print(f"[bold]Syncing results for {run_id}...[/bold]")
    local_dir = sync_run(run_id, bucket, environment, workdir)

    # Load and display manifest
    manifest = load_manifest(local_dir)
    if manifest:
        _print_manifest(console, manifest)

    results = load_results(local_dir)

    if not results:
        console.print(f"[red]No results found for run_id={run_id}[/red]")
        return

    console.print(f"[bold]Found {len(results)} systems.[/bold]")

    # Classification table
    type_counts: Counter[str] = Counter()
    for r in results:
        type_counts[r.system_type] += 1

    n = len(results)
    table = Table(title=f"System Classification (run_id={run_id}, N={n})")
    table.add_column("Type of Planetary System", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage (%)", justify="right", style="green")

    for sys_type_val in SystemType:
        count = type_counts.get(sys_type_val.value, 0)
        pct = 100.0 * count / n
        label = SYSTEM_TYPE_LABELS.get(sys_type_val.value, sys_type_val.value)
        table.add_row(label, str(count), f"{pct:.1f}")

    console.print(table)

    # Summary stats
    n_giants = sum(1 for r in results if r.consolidated.n_giant > 0)
    total_planets = sum(r.consolidated.n_giant + r.consolidated.n_terrestrial for r in results)
    console.print(f"\nSystems with giants: {n_giants}/{n} ({100*n_giants/n:.1f}%)")
    console.print(f"Total planets formed: {total_planets}")
    console.print(f"Mean planets per system: {total_planets/n:.1f}")
