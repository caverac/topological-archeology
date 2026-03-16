"""Main simulation loop for planet formation.

Evolves embryos in a protoplanetary disk over ~20 Myr:
solid accretion, gas accretion, migration, collisions, gas decay.
"""

from __future__ import annotations

import numpy as np
from disk_evolution.disk import DiskState, inner_boundary_au
from disk_evolution.growth import gas_accretion_rate, oligarchic_mass_earth, solid_accretion_rate
from disk_evolution.migration import migration_rate
from disk_evolution.models import (
    AU_CM,
    M_EARTH_G,
    ConsolidatedOutput,
    DiskParams,
    Embryo,
    ModelConfig,
    Planet,
    SystemArchitecture,
    consolidate,
)

# Maximum fractional mass change per timestep (stability limiter)
_MAX_FRAC_GROWTH: float = 0.05


def _hill_radius_au(a_au: float, mass_earth: float, stellar_mass_solar: float) -> float:
    """Hill radius in AU.

    Parameters
    ----------
    a_au : float
        Semi-major axis in AU.
    mass_earth : float
        Planet mass in Earth masses.
    stellar_mass_solar : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Hill radius in AU.
    """
    mass_ratio = mass_earth / (stellar_mass_solar * 332946.0)
    return float(a_au * (mass_ratio / 3.0) ** (1.0 / 3.0))


def _feeding_zone_mass_earth(
    a_au: float,
    sigma: float,
    mass_earth: float,
    stellar_mass: float,
) -> float:
    """Mass available in the feeding zone.

    Parameters
    ----------
    a_au : float
        Semi-major axis in AU.
    sigma : float
        Local surface density in g/cm^2.
    mass_earth : float
        Current planet mass in Earth masses.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Available mass in Earth masses.
    """
    r_hill = _hill_radius_au(a_au, max(mass_earth, 1e-6), stellar_mass)
    width_cm = 2.0 * r_hill * AU_CM
    r_cm = a_au * AU_CM
    area = 2.0 * np.pi * r_cm * width_cm
    return float(sigma * area / M_EARTH_G)


def _check_collisions(embryos: list[Embryo], stellar_mass: float) -> None:
    """Merge embryos that are within 3.5 Hill radii of each other.

    Parameters
    ----------
    embryos : list[Embryo]
        List of embryos (modified in place).
    stellar_mass : float
        Stellar mass in solar masses.
    """
    alive = [e for e in embryos if e.alive]
    alive.sort(key=lambda e: e.semi_major_axis)

    for i in range(len(alive) - 1):
        if not alive[i].alive:
            continue
        for j in range(i + 1, len(alive)):
            r_hill_i = _hill_radius_au(alive[i].semi_major_axis, alive[i].total_mass, stellar_mass)
            r_hill_j = _hill_radius_au(alive[j].semi_major_axis, alive[j].total_mass, stellar_mass)
            r_hill = max(r_hill_i, r_hill_j)
            separation = abs(alive[j].semi_major_axis - alive[i].semi_major_axis)

            if separation < 3.5 * r_hill:
                if alive[i].total_mass >= alive[j].total_mass:
                    alive[i].core_mass += alive[j].core_mass
                    alive[i].envelope_mass += alive[j].envelope_mass
                    alive[j].alive = False
                else:
                    alive[j].core_mass += alive[i].core_mass
                    alive[j].envelope_mass += alive[i].envelope_mass
                    alive[i].alive = False
                    break


def evolve_system(disk_params: DiskParams, config: ModelConfig) -> SystemArchitecture:
    """Run one full simulation of planet formation.

    Parameters
    ----------
    disk_params : DiskParams
        Initial conditions for the disk.
    config : ModelConfig
        Model configuration.

    Returns
    -------
    SystemArchitecture
        The resulting planetary system.
    """
    # Build precomputed disk state (expensive normalizations done once)
    disk = DiskState(disk_params, config)
    disk.__post_init__()

    # Initial embryo placement
    positions = disk.initial_embryo_positions()

    # Compute initial embryo masses
    r_arr = np.array(positions)
    sig_s_init = disk.sigma_solids(r_arr)

    embryos: list[Embryo] = []
    for pos, sig_s_val in zip(positions, sig_s_init):
        m_oli = oligarchic_mass_earth(float(sig_s_val), pos, disk_params.stellar_mass)
        embryos.append(Embryo(semi_major_axis=pos, core_mass=max(m_oli, 1e-4)))

    solids_consumed = [0.0] * len(embryos)

    t = 0.0
    dt = config.dt
    total_time = config.total_time
    inner_edge = inner_boundary_au(disk_params.stellar_mass) * 0.5

    while t < total_time:
        alive_indices = [i for i, e in enumerate(embryos) if e.alive]
        if not alive_indices:
            break

        # Gas decay
        gas_factor = np.exp(-t / disk_params.gas_dissipation_timescale)

        # Vectorized surface density evaluation (fast: no normalization recompute)
        positions_arr = np.array([embryos[i].semi_major_axis for i in alive_indices])
        current_sig_s = disk.sigma_solids(positions_arr)
        current_sig_g = disk.sigma_gas(positions_arr) * gas_factor

        for local_idx, global_idx in enumerate(alive_indices):
            embryo = embryos[global_idx]
            sig_s_local = float(current_sig_s[local_idx])
            sig_g_local = float(current_sig_g[local_idx])

            # Solid accretion with isolation mass limit
            fz_solid = _feeding_zone_mass_earth(
                embryo.semi_major_axis, sig_s_local, embryo.total_mass, disk_params.stellar_mass
            )
            available_solids = max(fz_solid - solids_consumed[global_idx], 0.0)

            core_rate = 0.0
            if available_solids > 0.0:
                core_rate = solid_accretion_rate(embryo, sig_s_local, disk_params.stellar_mass)
                dm_s = core_rate * dt
                dm_s = min(dm_s, available_solids, embryo.core_mass * _MAX_FRAC_GROWTH)
                dm_s = max(dm_s, 0.0)
                embryo.core_mass += dm_s
                solids_consumed[global_idx] += dm_s

            # Gas accretion
            if gas_factor > 1e-6:
                dm_g = gas_accretion_rate(embryo, core_accretion_rate_val=core_rate) * dt
                fz_gas = _feeding_zone_mass_earth(
                    embryo.semi_major_axis, sig_g_local, embryo.total_mass, disk_params.stellar_mass
                )
                dm_g = min(dm_g, fz_gas * 0.1, max(embryo.total_mass, 0.01) * _MAX_FRAC_GROWTH)
                dm_g = max(dm_g, 0.0)
                embryo.envelope_mass += dm_g

            # Migration
            da = migration_rate(
                embryo,
                sig_g_local,
                disk_params.stellar_mass,
                disk_params.characteristic_radius,
                disk_params.gas_dissipation_timescale,
                config.gamma,
                config.c_mig_i,
            )
            max_da = embryo.semi_major_axis * 0.05
            da_step = max(-max_da, min(da * dt, max_da))
            embryo.semi_major_axis += da_step

            if embryo.semi_major_axis < inner_edge:
                embryo.alive = False

        _check_collisions(embryos, disk_params.stellar_mass)
        t += dt

    planets = tuple(
        Planet(
            semi_major_axis=e.semi_major_axis,
            total_mass=e.total_mass,
            core_mass=e.core_mass,
        )
        for e in embryos
        if e.alive and e.total_mass > 1e-4
    )

    return SystemArchitecture(planets=planets, disk_params=disk_params)


def simulate_single(disk_params: DiskParams, config: ModelConfig) -> ConsolidatedOutput:
    """Run one simulation and return consolidated output.

    This is the clean Lambda-portable interface: input -> output.

    Parameters
    ----------
    disk_params : DiskParams
        Initial conditions for the disk.
    config : ModelConfig
        Model configuration.

    Returns
    -------
    ConsolidatedOutput
        Consolidated summary quantities.
    """
    architecture = evolve_system(disk_params, config)
    return consolidate(architecture)
