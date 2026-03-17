"""Collect simulation results from S3 and display summary."""

from __future__ import annotations

import json
from collections import Counter

import boto3
import click
from botocore.exceptions import ClientError
from disk_evolution.classify import SystemType
from mypy_boto3_s3 import S3Client
from rich.console import Console
from rich.table import Table

BUCKET_PREFIX = "topo-archeo"

SYSTEM_TYPE_LABELS: dict[str, str] = {
    SystemType.HOT_WARM_JUPITER.value: "Hot and warm Jupiters",
    SystemType.SOLAR.value: "Solar systems",
    SystemType.COLD_JUPITER.value: "Cold Jupiter",
    SystemType.COMBINED.value: "Combined systems",
    SystemType.LOW_MASS.value: "Low mass planet systems",
    SystemType.FAILED.value: "Failed planetary systems",
}


def _load_manifest(s3: S3Client, bucket: str, run_id: str) -> dict[str, object] | None:
    """Load the run manifest from S3, if it exists.

    Parameters
    ----------
    s3 : S3Client
        Boto3 S3 client.
    bucket : str
        S3 bucket name.
    run_id : str
        Run identifier.

    Returns
    -------
    dict[str, object] | None
        Manifest contents, or None if not found.
    """
    try:
        resp = s3.get_object(Bucket=bucket, Key=f"results/{run_id}/manifest.json")
        body: dict[str, object] = json.loads(resp["Body"].read().decode("utf-8"))
        return body
    except ClientError:
        return None


def _print_manifest(console: Console, manifest: dict[str, object]) -> None:
    """Print run metadata from the manifest.

    Parameters
    ----------
    console : Console
        Rich console.
    manifest : dict[str, object]
        Manifest contents.
    """
    config = manifest.get("config", {})
    assert isinstance(config, dict)
    console.print("[bold]Run metadata:[/bold]")
    console.print(f"  created_at: {manifest.get('created_at', 'unknown')}")
    console.print(f"  n_systems:  {manifest.get('n_systems', 'unknown')}")
    console.print(f"  seed:       {manifest.get('seed', 'unknown')}")
    console.print(f"  gamma:      {config.get('gamma', '?')}")
    console.print(f"  c_mig_i:    {config.get('c_mig_i', '?')}")
    console.print(f"  A:          {config.get('perturbation_amplitude', '?')}")
    console.print()


@click.command()
@click.option("--run-id", type=str, required=True, help="Run ID to collect results for.")
@click.option("--bucket", type=str, default="", help="S3 bucket name (auto-discovered if empty).")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
def collect(run_id: str, bucket: str, environment: str) -> None:
    """Collect simulation results from S3 and display classification table."""
    console = Console()

    if not bucket:
        bucket = f"{BUCKET_PREFIX}-{environment}-data"

    s3 = boto3.client("s3")
    prefix = f"results/{run_id}/"

    console.print(f"[bold]Listing results in s3://{bucket}/{prefix}...[/bold]")

    # Load and display manifest
    manifest = _load_manifest(s3, bucket, run_id)
    if manifest:
        _print_manifest(console, manifest)

    results: list[dict[str, object]] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".json") or key.endswith("manifest.json"):
                continue
            resp = s3.get_object(Bucket=bucket, Key=key)
            body = resp["Body"].read().decode("utf-8")
            results.append(json.loads(body))

    if not results:
        console.print(f"[red]No results found for run_id={run_id}[/red]")
        return

    console.print(f"[bold]Found {len(results)} systems.[/bold]")

    # Classification table
    type_counts: Counter[str] = Counter()
    for r in results:
        sys_type = str(r.get("system_type", "unknown"))
        type_counts[sys_type] += 1

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
    n_giants = sum(1 for r in results if _get_int(r, "n_giant") > 0)
    total_planets = sum(_get_int(r, "n_giant") + _get_int(r, "n_terrestrial") for r in results)
    console.print(f"\nSystems with giants: {n_giants}/{n} ({100*n_giants/n:.1f}%)")
    console.print(f"Total planets formed: {total_planets}")
    console.print(f"Mean planets per system: {total_planets/n:.1f}")


def _get_int(result: dict[str, object], key: str) -> int:
    """Extract an integer from a nested consolidated dict."""
    consolidated = result.get("consolidated", {})
    if isinstance(consolidated, dict):
        val = consolidated.get(key, 0)
        return int(str(val).split(".", maxsplit=1)[0]) if val is not None else 0
    return 0
