"""Tests for the experiments CLI."""

import json
from unittest.mock import MagicMock, patch

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
    # Only the .json file should be fetched, not the .txt
    mock_s3.get_object.assert_called_once()


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
