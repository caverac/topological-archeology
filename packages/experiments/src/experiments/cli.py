"""Click-based CLI entry point."""

import click
from experiments.commands.collect import collect
from experiments.commands.hello import hello
from experiments.commands.persistence import persistence
from experiments.commands.plot_bifurcation import plot_bifurcation
from experiments.commands.plot_calibration import plot_calibration
from experiments.commands.plot_persistence import plot_persistence
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
main.add_command(plot_bifurcation)
main.add_command(plot_persistence)
main.add_command(plot_calibration)
