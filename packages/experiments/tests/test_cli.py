"""Tests for the experiments CLI."""

import json
import math
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from click.testing import CliRunner
from experiments.cli import main


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


@patch("experiments.commands.collect.boto3")
def test_collect_no_results(mock_boto3: MagicMock) -> None:
    """Verify collect handles empty results."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    # Manifest doesn't exist
    mock_s3.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject")
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": []}]

    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--run-id", "nonexistent"])
    assert result.exit_code == 0
    assert "No results found" in result.output


@patch("experiments.commands.collect.boto3")
def test_collect_displays_results(mock_boto3: MagicMock) -> None:
    """Verify collect reads S3 objects and displays classification table."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    system_result = {
        "system_index": 0,
        "system_type": "low_mass",
        "consolidated": {"n_giant": 0, "n_terrestrial": 5},
    }
    body_bytes = json.dumps(system_result).encode("utf-8")

    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "results/run-123/000000.json"},
                {"Key": "results/run-123/some-other-file.txt"},
            ]
        }
    ]

    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    mock_s3.get_object.return_value = {"Body": mock_body}

    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--run-id", "run-123"])
    assert result.exit_code == 0
    assert "Found 1 systems" in result.output
    assert "System Classification" in result.output
    assert "Low mass planet systems" in result.output
    # Manifest + one result file fetched, not the .txt
    assert mock_s3.get_object.call_count == 2


@patch("experiments.commands.collect.boto3")
def test_collect_handles_missing_consolidated(mock_boto3: MagicMock) -> None:
    """Verify collect handles results without consolidated data."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    system_result = {"system_index": 0, "system_type": "failed", "consolidated": "corrupt"}
    body_bytes = json.dumps(system_result).encode("utf-8")

    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": [{"Key": "results/run-x/000000.json"}]}]
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    mock_s3.get_object.return_value = {"Body": mock_body}

    runner = CliRunner()
    result = runner.invoke(main, ["collect", "--run-id", "run-x"])
    assert result.exit_code == 0
    assert "Found 1 systems" in result.output


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


@patch("experiments.commands.persistence.boto3")
def test_persistence_no_data(mock_boto3: MagicMock) -> None:
    """Verify persistence handles empty results."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_s3.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject")
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": []}]

    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--run-id", "empty"])
    assert result.exit_code == 0
    assert "No data found" in result.output


@patch("experiments.commands.persistence.boto3")
def test_persistence_computes_homology(mock_boto3: MagicMock) -> None:
    """Verify persistence computes and displays H0/H1 results."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    # Create 30 mock systems on a circle (produces H1) plus a non-json file

    n_points = 30
    contents = []
    bodies = []
    for i in range(n_points):
        key = f"results/run-test/{i:06d}.json"
        contents.append({"Key": key})
        angle = 2 * math.pi * i / n_points
        system = {
            "system_index": i,
            "system_type": "low_mass",
            "consolidated": {
                "n_giant": 0,
                "n_terrestrial": 10,
                "total_terrestrial_mass": 5.0 * math.cos(angle),
                "avg_terrestrial_mass": 5.0 * math.sin(angle),
                "mass_efficiency": 0.01,
                "center_of_mass": 3.0,
            },
        }
        bodies.append(json.dumps(system).encode("utf-8"))
    # Add a non-json file that should be skipped
    contents.append({"Key": "results/run-test/metadata.txt"})

    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": contents}]

    # Manifest is fetched first, then each system result
    manifest = json.dumps({"run_id": "run-test", "config": {"gamma": 1.0}}).encode("utf-8")
    all_bodies = [manifest] + bodies
    call_count = 0

    def get_object_side_effect(**_kwargs: object) -> dict[str, object]:
        nonlocal call_count
        mock_body = MagicMock()
        mock_body.read.return_value = all_bodies[call_count]
        call_count += 1
        return {"Body": mock_body}

    mock_s3.get_object.side_effect = get_object_side_effect

    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--run-id", "run-test"])
    assert result.exit_code == 0
    assert f"{n_points} systems" in result.output
    assert "Persistence Summary" in result.output
    assert "H0" in result.output
    assert "H1" in result.output
    # Circular data should produce H1 features with reported lifetimes
    assert "Significant loops" in result.output


@patch("experiments.commands.persistence.boto3")
def test_persistence_with_few_points_no_h1(mock_boto3: MagicMock) -> None:
    """Verify persistence handles case with no H1 features."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    # 3 collinear points -- no loops possible
    systems = []
    for i in range(3):
        systems.append(
            {
                "system_type": "low_mass",
                "consolidated": {
                    "n_giant": 0,
                    "n_terrestrial": i + 1,
                    "total_terrestrial_mass": float(i),
                    "avg_terrestrial_mass": float(i) * 0.1,
                    "mass_efficiency": float(i) * 0.01,
                    "center_of_mass": float(i),
                },
            }
        )

    contents = [{"Key": f"results/run-noh1/{i:06d}.json"} for i in range(3)]
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": contents}]

    manifest = {"run_id": "run-noh1", "config": {"gamma": 1.0}}
    all_items = [manifest] + systems
    idx = 0

    def get_side(**_kwargs: object) -> dict[str, object]:
        nonlocal idx
        body = MagicMock()
        body.read.return_value = json.dumps(all_items[idx]).encode("utf-8")
        idx += 1
        return {"Body": body}

    mock_s3.get_object.side_effect = get_side

    runner = CliRunner()
    result = runner.invoke(main, ["persistence", "--run-id", "run-noh1"])
    assert result.exit_code == 0
    assert "No H1 features" in result.output


@patch("experiments.commands.persistence.boto3")
def test_persistence_skips_corrupt_consolidated(mock_boto3: MagicMock) -> None:
    """Verify persistence skips systems with non-dict consolidated."""
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    # One valid, one corrupt
    systems = [
        {
            "consolidated": {
                "n_giant": 0,
                "n_terrestrial": 5,
                "total_terrestrial_mass": 1.0,
                "avg_terrestrial_mass": 0.2,
                "mass_efficiency": 0.01,
                "center_of_mass": 3.0,
            },
            "system_type": "low_mass",
        },
        {"consolidated": "corrupt", "system_type": "failed"},
    ]

    contents = [{"Key": f"results/run-c/{i:06d}.json"} for i in range(2)]

    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{"Contents": contents}]

    manifest = {"run_id": "run-c", "config": {"gamma": 1.0}}
    all_items = [manifest] + systems
    idx = 0

    def get_side(**_kwargs: object) -> dict[str, object]:
        nonlocal idx
        body = MagicMock()
        body.read.return_value = json.dumps(all_items[idx]).encode("utf-8")
        idx += 1
        return {"Body": body}

    mock_s3.get_object.side_effect = get_side

    runner = CliRunner()
    # Only 1 valid system -- ripser needs at least 2 points, so this will have 1 system
    result = runner.invoke(main, ["persistence", "--run-id", "run-c"])
    assert result.exit_code == 0
    assert "1 systems" in result.output
