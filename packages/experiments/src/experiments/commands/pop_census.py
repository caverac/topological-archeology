"""Reproduce Tables 2-4 from Miguel et al. (2011).

Runs population synthesis for a given (gamma, c_mig_i) configuration
and classifies systems into the six types defined in Section 3.1.
"""

from __future__ import annotations

from collections import Counter

import click
from disk_evolution.classify import SystemType, classify
from disk_evolution.models import ModelConfig
from disk_evolution.priors import draw_population
from disk_evolution.simulate import evolve_system
from rich.console import Console
from rich.table import Table

SYSTEM_TYPE_LABELS: dict[SystemType, str] = {
    SystemType.HOT_WARM_JUPITER: "Hot and warm Jupiters",
    SystemType.SOLAR: "Solar systems",
    SystemType.COLD_JUPITER: "Cold Jupiter",
    SystemType.COMBINED: "Combined systems",
    SystemType.LOW_MASS: "Low mass planet systems",
    SystemType.FAILED: "Failed planetary systems",
}


@click.command(name="pop-census")
@click.option("--gamma", type=float, default=1.0, help="Disk density profile exponent.")
@click.option("--c-mig-i", type=float, default=0.0, help="Type I migration delay factor (0=off).")
@click.option("--n-systems", type=int, default=100, help="Number of systems to simulate.")
@click.option("--seed", type=int, default=42, help="Random seed.")
def pop_census(gamma: float, c_mig_i: float, n_systems: int, seed: int) -> None:
    """Run population synthesis and classify systems (Miguel+ 2011, Tables 2-4)."""
    console = Console()

    config = ModelConfig(gamma=gamma, c_mig_i=c_mig_i, perturbation_amplitude=0.0)

    console.print(f"[bold]Drawing {n_systems} disk initial conditions...[/bold]")
    disk_params_list = draw_population(n_systems, config, seed=seed)

    console.print(f"[bold]Simulating {n_systems} systems (gamma={gamma}, c_mig_i={c_mig_i})...[/bold]")

    counts: Counter[SystemType] = Counter()
    for i, dp in enumerate(disk_params_list):
        if (i + 1) % max(1, n_systems // 10) == 0:
            console.print(f"  [{i + 1}/{n_systems}]")
        arch = evolve_system(dp, config)
        sys_type = classify(arch)
        counts[sys_type] += 1

    table = Table(title=f"System Classification (gamma={gamma}, c_mig_i={c_mig_i}, N={n_systems})")
    table.add_column("Type of Planetary System", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage (%)", justify="right", style="green")

    for sys_type in SystemType:
        count = counts.get(sys_type, 0)
        pct = 100.0 * count / n_systems if n_systems > 0 else 0.0
        table.add_row(SYSTEM_TYPE_LABELS[sys_type], str(count), f"{pct:.1f}")

    console.print(table)
