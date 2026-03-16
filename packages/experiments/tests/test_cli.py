"""Tests for the experiments CLI."""

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
