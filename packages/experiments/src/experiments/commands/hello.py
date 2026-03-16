"""Hello-world command."""

import click
from rich.console import Console
from topo_archeo.hello import hello as topo_hello


@click.command()
def hello() -> None:
    """Print a hello-world greeting."""
    console = Console()
    console.print(f"[bold green]{topo_hello()}[/bold green]")
