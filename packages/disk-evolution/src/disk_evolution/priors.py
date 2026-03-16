"""Prior distributions for Monte Carlo population synthesis.

Draws initial conditions from the distributions specified in
Miguel et al. (2011), Section 3.
"""

from __future__ import annotations

import numpy as np
from disk_evolution.disk import is_stable
from disk_evolution.models import DiskParams, ModelConfig
from numpy.random import Generator


def draw_disk_params(rng: Generator, config: ModelConfig, max_attempts: int = 1000) -> DiskParams:
    """Draw a single set of disk initial conditions from the priors.

    Rejects draws that produce gravitationally unstable disks
    (Toomre Q < 1 or M_disk > 0.2 M_star).

    Parameters
    ----------
    rng : Generator
        NumPy random number generator.
    config : ModelConfig
        Model configuration (needed for stability check).
    max_attempts : int
        Maximum rejection sampling attempts.

    Returns
    -------
    DiskParams
        A valid set of disk initial conditions.

    Raises
    ------
    RuntimeError
        If no stable disk is found within max_attempts.
    """
    for _ in range(max_attempts):
        params = _draw_unchecked(rng)
        if is_stable(params, config):
            return params

    raise RuntimeError(f"No stable disk found after {max_attempts} attempts")


def _draw_unchecked(rng: Generator) -> DiskParams:
    """Draw disk parameters without stability check.

    Parameters
    ----------
    rng : Generator
        NumPy random number generator.

    Returns
    -------
    DiskParams
        Unchecked disk initial conditions.
    """
    # Stellar mass: log-uniform in [0.7, 1.4] M_sun
    log_m_star = rng.uniform(np.log10(0.7), np.log10(1.4))
    stellar_mass = 10.0**log_m_star

    # Disk mass: log-Gaussian with mu=-2.05, sigma=0.85 (in log10 M_sun)
    log_disk_mass = rng.normal(-2.05, 0.85)
    disk_mass = 10.0**log_disk_mass

    # Characteristic radius: log-Gaussian with mu=3.8, sigma=0.18 (in log10 AU)
    # Actually mu and sigma refer to the underlying log-Gaussian
    log_a_c = rng.normal(np.log10(3.8), 0.18)
    characteristic_radius = 10.0**log_a_c

    # Metallicity: Gaussian with mu=-0.02, sigma=0.22
    metallicity = rng.normal(-0.02, 0.22)

    # Gas dissipation timescale: log-uniform in [1e6, 1e7] years
    log_tau = rng.uniform(6.0, 7.0)
    gas_dissipation_timescale = 10.0**log_tau

    return DiskParams(
        stellar_mass=stellar_mass,
        disk_mass=disk_mass,
        characteristic_radius=characteristic_radius,
        metallicity=metallicity,
        gas_dissipation_timescale=gas_dissipation_timescale,
    )


def draw_population(
    n_systems: int,
    config: ModelConfig,
    seed: int = 42,
) -> list[DiskParams]:
    """Draw initial conditions for a population of systems.

    Parameters
    ----------
    n_systems : int
        Number of systems to draw.
    config : ModelConfig
        Model configuration.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    list[DiskParams]
        List of disk initial conditions.
    """
    rng = np.random.default_rng(seed)
    return [draw_disk_params(rng, config) for _ in range(n_systems)]
