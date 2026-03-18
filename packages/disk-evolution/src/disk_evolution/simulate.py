"""Main simulation loop for planet formation.

Evolves embryos in a protoplanetary disk over ~20 Myr:
solid accretion, gas accretion, migration, collisions, gas decay.
"""

from __future__ import annotations

import numpy as np
from disk_evolution.disk import DiskState, inner_boundary_au
from disk_evolution.dynamics import evolve_eccentricity_inclination
from disk_evolution.growth import SEED_MASS_EARTH, gas_accretion_rate, solid_accretion_rate
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

# Maximum fractional mass change per timestep for gas accretion (stability limiter).
# Solid accretion is limited by the feeding zone mass instead.
_MAX_GAS_FRAC_GROWTH: float = 0.5


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
    # Feeding zone width = 10 * R_Hill (embryo spacing Delta_a, Eq. 7)
    width_cm = 10.0 * r_hill * AU_CM
    r_cm = a_au * AU_CM
    area = 2.0 * np.pi * r_cm * width_cm
    return float(sigma * area / M_EARTH_G)


def _check_collisions(embryos: list[Embryo], stellar_mass: float) -> None:
    """Merge embryos that are within 3.5 Hill radii of each other.

    Runs multiple passes until no more mergers occur, capturing
    cascade mergers where one merger changes Hill radii of neighbors.

    Parameters
    ----------
    embryos : list[Embryo]
        List of embryos (modified in place).
    stellar_mass : float
        Stellar mass in solar masses.
    """
    while True:
        merged_any = False
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
                    merged_any = True
                    if alive[i].total_mass >= alive[j].total_mass:
                        alive[i].core_mass += alive[j].core_mass
                        alive[i].envelope_mass += alive[j].envelope_mass
                        alive[j].alive = False
                    else:
                        alive[j].core_mass += alive[i].core_mass
                        alive[j].envelope_mass += alive[i].envelope_mass
                        alive[i].alive = False
                        break

        if not merged_any:
            break


def _update_embryo(
    embryo: Embryo,
    global_idx: int,
    sig_s_local: float,
    sig_g_local: float,
    gas_factor: float,
    dt: float,
    inner_edge: float,
    disk_params: DiskParams,
    config: ModelConfig,
    solids_consumed: list[float],
    eccentricities: list[float],
    inclinations: list[float],
) -> None:
    """Advance one embryo by one timestep.

    Handles eccentricity/inclination evolution, solid accretion,
    gas accretion, and migration. Modifies embryo and tracking
    lists in place.

    Parameters
    ----------
    embryo : Embryo
        Embryo to update.
    global_idx : int
        Index into the tracking arrays.
    sig_s_local : float
        Local solid surface density in g/cm^2.
    sig_g_local : float
        Local gas surface density in g/cm^2 (already decayed).
    gas_factor : float
        Gas decay factor exp(-t/tau).
    dt : float
        Timestep in years.
    inner_edge : float
        Inner boundary in AU.
    disk_params : DiskParams
        Disk initial conditions.
    config : ModelConfig
        Model configuration.
    solids_consumed : list[float]
        Cumulative solids consumed per embryo.
    eccentricities : list[float]
        Planetesimal eccentricities per embryo.
    inclinations : list[float]
        Planetesimal inclinations per embryo.
    """
    # Feeding zone
    fz_solid = _feeding_zone_mass_earth(
        embryo.semi_major_axis, sig_s_local, embryo.total_mass, disk_params.stellar_mass
    )
    available_solids = max(fz_solid - solids_consumed[global_idx], 0.0)

    # Evolve planetesimal eccentricity and inclination
    ecc_local = eccentricities[global_idx]
    inc_local = inclinations[global_idx]
    if sig_g_local > 0:
        ecc_local, inc_local = evolve_eccentricity_inclination(
            ecc_local,
            inc_local,
            embryo.total_mass,
            embryo.semi_major_axis,
            sig_g_local,
            disk_params.stellar_mass,
            config.gamma,
            dt,
        )
        eccentricities[global_idx] = ecc_local
        inclinations[global_idx] = inc_local

    # Solid accretion
    core_rate = 0.0
    if available_solids > 0.0:
        core_rate = solid_accretion_rate(embryo, sig_s_local, disk_params.stellar_mass, ecc=ecc_local, inc=inc_local)
        dm_s = min(core_rate * dt, available_solids)
        dm_s = max(dm_s, 0.0)
        embryo.core_mass += dm_s
        solids_consumed[global_idx] += dm_s

    # Gas accretion
    if gas_factor > 1e-6:
        dm_g = gas_accretion_rate(embryo, core_accretion_rate_val=core_rate) * dt
        fz_gas = _feeding_zone_mass_earth(
            embryo.semi_major_axis, sig_g_local, embryo.total_mass, disk_params.stellar_mass
        )
        dm_g = min(dm_g, fz_gas * 0.1, max(embryo.total_mass, 0.01) * _MAX_GAS_FRAC_GROWTH)
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

    # Seed embryos at fixed mass (Fortier 2013, Sec. 5.1)
    embryos: list[Embryo] = []
    for pos in positions:
        embryos.append(Embryo(semi_major_axis=pos, core_mass=SEED_MASS_EARTH))

    solids_consumed = [0.0] * len(embryos)

    # Planetesimal eccentricity and inclination per embryo
    # Initial values: small equilibrium estimate
    n_embryos = len(embryos)
    eccentricities = [1e-3] * n_embryos
    inclinations = [5e-4] * n_embryos

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
            _update_embryo(
                embryos[global_idx],
                global_idx,
                float(current_sig_s[local_idx]),
                float(current_sig_g[local_idx]),
                gas_factor,
                dt,
                inner_edge,
                disk_params,
                config,
                solids_consumed,
                eccentricities,
                inclinations,
            )

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
