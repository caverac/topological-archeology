"""Click-based CLI entry point."""

import click
from experiments.commands.hello import hello


@click.group()
def main() -> None:
    """Research CLI for topological archeology experiments and figures."""


main.add_command(hello)
