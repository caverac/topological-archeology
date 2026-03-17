"""Click-based CLI entry point."""

import click
from experiments.commands.collect import collect
from experiments.commands.hello import hello
from experiments.commands.persistence import persistence
from experiments.commands.pop_census import pop_census
from experiments.commands.submit import submit


@click.group()
def main() -> None:
    """Research CLI for topological archeology experiments and figures."""


main.add_command(hello)
main.add_command(pop_census)
main.add_command(submit)
main.add_command(collect)
main.add_command(persistence)
