"""Local cache for S3 results.

Mirrors the S3 structure under a local work directory, downloading
files only if they don't already exist locally.
"""

from __future__ import annotations

from pathlib import Path

import boto3
from experiments._models import RunManifest, SimulationResult
from pydantic import ValidationError
from rich.console import Console

DEFAULT_WORKDIR = "/tmp/topological-archeology"
BUCKET_PREFIX = "topo-archeo"

console = Console()


def _ensure_workdir(workdir: str) -> Path:
    """Create the work directory if needed.

    Parameters
    ----------
    workdir : str
        Local work directory path.

    Returns
    -------
    Path
        Path object for the work directory.
    """
    p = Path(workdir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sync_run(
    run_id: str,
    bucket: str = "",
    environment: str = "development",
    workdir: str = DEFAULT_WORKDIR,
) -> Path:
    """Sync a run's results from S3 to local cache.

    Only downloads files that don't exist locally. Returns the
    local directory containing the cached results.

    Parameters
    ----------
    run_id : str
        Run identifier.
    bucket : str
        S3 bucket name. Auto-discovered if empty.
    environment : str
        Deployment environment.
    workdir : str
        Local work directory.

    Returns
    -------
    Path
        Local directory containing cached result files.
    """
    if not bucket:
        bucket = f"{BUCKET_PREFIX}-{environment}-data"

    base = _ensure_workdir(workdir)
    local_dir = base / "results" / run_id
    local_dir.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3")
    prefix = f"results/{run_id}/"

    # Count existing local files
    existing = set(f.name for f in local_dir.glob("*.json"))

    # List remote files and download missing ones
    downloaded = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key.split("/")[-1]
            if not filename.endswith(".json"):
                continue
            if filename in existing:
                continue
            local_path = local_dir / filename
            s3.download_file(bucket, key, str(local_path))
            downloaded += 1

    total = len(list(local_dir.glob("*.json")))
    if downloaded > 0:
        console.print(f"  Synced {downloaded} new files ({total} total) to {local_dir}")
    else:
        console.print(f"  Cache hit: {total} files in {local_dir}")

    return local_dir


def load_results(local_dir: Path) -> list[SimulationResult]:
    """Load all result JSON files from a local directory.

    Parameters
    ----------
    local_dir : Path
        Directory containing result JSON files.

    Returns
    -------
    list[SimulationResult]
        List of parsed simulation results.
    """
    results: list[SimulationResult] = []
    for f in sorted(local_dir.glob("*.json")):
        if f.name == "manifest.json":
            continue
        try:
            results.append(SimulationResult.model_validate_json(f.read_text()))
        except ValidationError:
            console.print(f"  [yellow]Skipping invalid result: {f.name}[/yellow]")
    return results


def load_manifest(local_dir: Path) -> RunManifest | None:
    """Load the manifest file from a local directory.

    Parameters
    ----------
    local_dir : Path
        Directory containing the manifest.

    Returns
    -------
    RunManifest | None
        Manifest contents, or None if not found.
    """
    manifest_path = local_dir / "manifest.json"
    if manifest_path.exists():
        return RunManifest.model_validate_json(manifest_path.read_text())
    return None


def load_point_cloud(local_dir: Path) -> tuple[list[list[float]], list[str]]:
    """Load consolidated vectors and system types from cached results.

    Parameters
    ----------
    local_dir : Path
        Directory containing result JSON files.

    Returns
    -------
    tuple[list[list[float]], list[str]]
        Rows of consolidated vectors, and system type labels.
    """
    rows: list[list[float]] = []
    system_types: list[str] = []
    for result in load_results(local_dir):
        c = result.consolidated
        rows.append(
            [
                float(c.n_giant),
                float(c.n_terrestrial),
                c.total_terrestrial_mass,
                c.avg_terrestrial_mass,
                c.mass_efficiency,
                c.center_of_mass,
            ]
        )
        system_types.append(result.system_type)
    return rows, system_types
