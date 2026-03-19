"""Tests for the experiments CLI."""

import json
import math
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from experiments.cli import main


def _make_system(
    index: int = 0,
    system_type: str = "low_mass",
    n_giant: int = 0,
    n_terrestrial: int = 5,
    total_terrestrial_mass: float = 1.0,
    avg_terrestrial_mass: float = 0.2,
    mass_efficiency: float = 0.01,
    center_of_mass: float = 3.0,
) -> dict[str, Any]:
    """Build a valid simulation result dict for testing."""
    return {
        "system_index": index,
        "system_type": system_type,
        "disk_params": {
            "stellar_mass": 1.0,
            "disk_mass": 0.05,
            "characteristic_radius": 30.0,
            "metallicity": 0.0,
            "gas_dissipation_timescale": 3e6,
        },
        "config": {"gamma": 1.0, "c_mig_i": 0.0, "perturbation_amplitude": 0.0},
        "planets": [],
        "consolidated": {
            "n_giant": n_giant,
            "n_terrestrial": n_terrestrial,
            "total_terrestrial_mass": total_terrestrial_mass,
            "avg_terrestrial_mass": avg_terrestrial_mass,
            "mass_efficiency": mass_efficiency,
            "center_of_mass": center_of_mass,
        },
    }


def _make_manifest(run_id: str = "run-test", gamma: float = 1.0) -> dict[str, Any]:
    """Build a valid manifest dict for testing."""
    return {
        "run_id": run_id,
        "config": {"gamma": gamma, "c_mig_i": 0.0, "perturbation_amplitude": 0.0},
    }


def _write_run_files(
    workdir: Path,
    run_id: str,
    systems: list[dict[str, Any]],
    manifest: dict[str, Any] | None = None,
) -> Path:
    """Write simulation result files to a local directory for testing."""
    local_dir = workdir / "results" / run_id
    local_dir.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        (local_dir / "manifest.json").write_text(json.dumps(manifest))
    for i, system in enumerate(systems):
        (local_dir / f"{i:06d}.json").write_text(json.dumps(system))
    return local_dir


def test_main_group_help() -> None:
    """Verify the CLI group shows help text."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Research CLI" in result.output


def test_hello_command() -> None:
    """Verify the hello command prints a greeting."""
    runner = CliRunner()
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
    assert "Hello from topo-archeo!" in result.output


def test_pop_census_help() -> None:
    """Verify pop-census command has help text."""
    runner = CliRunner()
    result = runner.invoke(main, ["pop-census", "--help"])
    assert result.exit_code == 0
    assert "Miguel" in result.output


def test_pop_census_runs() -> None:
    """Verify pop-census runs with minimal settings and produces a table."""
    runner = CliRunner()
    result = runner.invoke(main, ["pop-census", "--n-systems", "3", "--seed", "0"])
    assert result.exit_code == 0
    assert "System Classification" in result.output
    assert "Percentage" in result.output


def test_submit_help() -> None:
    """Verify submit command has help text."""
    runner = CliRunner()
    result = runner.invoke(main, ["submit", "--help"])
    assert result.exit_code == 0
    assert "Submit" in result.output


@patch("experiments.commands.submit.boto3")
def test_submit_sends_messages(mock_boto3: MagicMock) -> None:
    """Verify submit draws params and sends SQS messages."""
    mock_sqs = MagicMock()
    mock_boto3.client.return_value = mock_sqs
    mock_sqs.get_queue_url.return_value = {"QueueUrl": "https://sqs.us-east-1.amazonaws.com/123/test"}

    runner = CliRunner()
    result = runner.invoke(main, ["submit", "--n-systems", "3", "--seed", "0", "--run-id", "test-run"])
    assert result.exit_code == 0
    assert "3 jobs submitted" in result.output
    assert mock_sqs.send_message.call_count == 3

    # Verify manifest was written to S3
    mock_sqs.put_object.assert_called_once()
    manifest_call = mock_sqs.put_object.call_args
    assert "manifest.json" in manifest_call.kwargs["Key"]
    manifest_body = json.loads(manifest_call.kwargs["Body"])
    assert manifest_body["run_id"] == "test-run"
    assert manifest_body["n_systems"] == 3
    assert manifest_body["seed"] == 0
    assert "config" in manifest_body

    # Verify message structure
    call_args = mock_sqs.send_message.call_args_list[0]
    body = json.loads(call_args.kwargs["MessageBody"])
    assert "disk_params" in body
    assert "config" in body
    assert body["run_id"] == "test-run"
    assert body["system_index"] == 0
    assert "stellar_mass" in body["disk_params"]


def test_collect_help() -> None:
    """Verify collect command has help text."""
    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--help"])
    assert result.exit_code == 0
    assert "Collect" in result.output


@patch("experiments._cache.boto3")
def test_collect_no_results(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify collect handles empty results."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": []}]

    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--run-id", "nonexistent", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No results found" in result.output


@patch("experiments._cache.boto3")
def test_collect_displays_results(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify collect reads cached files and displays classification table."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": [{"Key": "results/run-123/000000.json"}]}]

    # Write files to local cache so load_results can read them
    _write_run_files(tmp_path, "run-123", [_make_system()])

    # Make download_file a no-op (files already on disk)
    mock_s3.download_file.return_value = None

    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--run-id", "run-123", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Found 1 systems" in result.output
    assert "System Classification" in result.output
    assert "Low mass planet systems" in result.output


@patch("experiments._cache.boto3")
def test_collect_handles_missing_consolidated(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify collect skips results with invalid JSON structure."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": [{"Key": "results/run-x/000000.json"}]}]

    # Write a corrupt file directly
    local_dir = tmp_path / "results" / "run-x"
    local_dir.mkdir(parents=True)
    corrupt = {"system_index": 0, "system_type": "failed", "consolidated": "corrupt"}
    (local_dir / "000000.json").write_text(json.dumps(corrupt))

    mock_s3.download_file.return_value = None

    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--run-id", "run-x", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    # Corrupt result is skipped by Pydantic validation
    assert "Skipping invalid result" in result.output


@patch("experiments.commands.submit.boto3")
def test_submit_auto_generates_run_id(mock_boto3: MagicMock) -> None:
    """Verify submit generates a run_id when not provided."""
    mock_sqs = MagicMock()
    mock_boto3.client.return_value = mock_sqs
    mock_sqs.get_queue_url.return_value = {"QueueUrl": "https://sqs/test"}

    runner = CliRunner()
    result = runner.invoke(main, ["submit", "--n-systems", "1", "--seed", "0"])
    assert result.exit_code == 0
    assert "1 jobs submitted" in result.output
    assert "run-" in result.output


def test_persistence_help() -> None:
    """Verify persistence command has help text."""
    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--help"])
    assert result.exit_code == 0
    assert "persistent homology" in result.output.lower()


@patch("experiments._cache.boto3")
def test_persistence_no_data(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify persistence handles empty results."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": []}]

    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--run-id", "empty", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No data found" in result.output


@patch("experiments._cache.boto3")
def test_persistence_computes_homology(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify persistence computes and displays H0/H1 results."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator

    # Create 30 mock systems on a circle (produces H1)
    n_points = 30
    systems = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        systems.append(
            _make_system(
                index=i,
                n_terrestrial=10,
                total_terrestrial_mass=5.0 * math.cos(angle),
                avg_terrestrial_mass=5.0 * math.sin(angle),
            )
        )

    contents = [{"Key": f"results/run-test/{i:06d}.json"} for i in range(n_points)]
    mock_paginator.paginate.return_value = [{"Contents": contents}]
    mock_s3.download_file.return_value = None

    _write_run_files(tmp_path, "run-test", systems, _make_manifest())

    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--run-id", "run-test", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert f"{n_points} systems" in result.output
    assert "Persistence Summary" in result.output
    assert "H0" in result.output
    assert "H1" in result.output
    # Circular data should produce H1 features with reported lifetimes
    assert "Significant loops" in result.output


@patch("experiments._cache.boto3")
def test_persistence_with_few_points_no_h1(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify persistence handles case with no H1 features."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator

    # 3 collinear points -- no loops possible
    systems = []
    for i in range(3):
        systems.append(
            _make_system(
                index=i,
                n_terrestrial=i + 1,
                total_terrestrial_mass=float(i),
                avg_terrestrial_mass=float(i) * 0.1,
                mass_efficiency=float(i) * 0.01,
                center_of_mass=float(i),
            )
        )

    contents = [{"Key": f"results/run-noh1/{i:06d}.json"} for i in range(3)]
    mock_paginator.paginate.return_value = [{"Contents": contents}]
    mock_s3.download_file.return_value = None

    _write_run_files(tmp_path, "run-noh1", systems, _make_manifest(run_id="run-noh1"))

    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--run-id", "run-noh1", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No H1 features" in result.output


@patch("experiments._cache.boto3")
def test_persistence_skips_corrupt_consolidated(mock_boto3: MagicMock, tmp_path: Path) -> None:
    """Verify persistence skips systems with invalid JSON structure."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator

    contents = [{"Key": f"results/run-c/{i:06d}.json"} for i in range(2)]
    mock_paginator.paginate.return_value = [{"Contents": contents}]
    mock_s3.download_file.return_value = None

    # Write one valid and one corrupt file
    local_dir = tmp_path / "results" / "run-c"
    local_dir.mkdir(parents=True)
    (local_dir / "manifest.json").write_text(json.dumps(_make_manifest(run_id="run-c")))
    (local_dir / "000000.json").write_text(json.dumps(_make_system()))
    (local_dir / "000001.json").write_text(json.dumps({"consolidated": "corrupt", "system_type": "failed"}))

    runner = CliRunner()
    # Only 1 valid system -- ripser needs at least 2 points, so this will have 1 system
    result = runner.invoke(main, ["persistence", "--run-id", "run-c", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert "1 systems" in result.output
