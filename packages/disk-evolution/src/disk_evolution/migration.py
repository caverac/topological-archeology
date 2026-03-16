"""Planetary migration: Type I and Type II.

Implements Eqs. 13-16 from Miguel et al. (2011).
"""

from __future__ import annotations

import numpy as np
from disk_evolution.models import AU_CM, G_CGS, K_BOLTZ, M_EARTH_G, M_PROTON, M_SUN_G, Embryo


def _disk_aspect_ratio(r_au: float, stellar_mass: float) -> float:
    """Compute h(r)/r, the disk aspect ratio.

    Parameters
    ----------
    r_au : float
        Radial position in AU.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Disk aspect ratio h/r.
    """
    luminosity = stellar_mass**4.0
    temp = 280.0 * (r_au ** (-0.5)) * luminosity**0.25
    mu = 2.34
    cs_sq = K_BOLTZ * temp / (mu * M_PROTON)
    r_cm = r_au * AU_CM
    vk_sq = G_CGS * stellar_mass * M_SUN_G / r_cm
    return float(np.sqrt(cs_sq / vk_sq))


def type_i_migration_rate(
    embryo: Embryo,
    sigma_g: float,
    stellar_mass: float,
    gamma: float,
    characteristic_radius: float,
    c_mig_i: float,
) -> float:
    """Type I migration rate da/dt (Eq. 13).

    Parameters
    ----------
    embryo : Embryo
        Current embryo state.
    sigma_g : float
        Local gas surface density in g/cm^2.
    stellar_mass : float
        Stellar mass in solar masses.
    gamma : float
        Density profile exponent.
    characteristic_radius : float
        Characteristic radius a_c in AU.
    c_mig_i : float
        Migration delay factor. 0 disables migration.

    Returns
    -------
    float
        Migration rate in AU/year (negative = inward).
    """
    if c_mig_i == 0.0:
        return 0.0

    r_au = embryo.semi_major_axis
    r_cm = r_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    m_total_g = embryo.total_mass * M_EARTH_G

    h_over_r = _disk_aspect_ratio(r_au, stellar_mass)
    cs = h_over_r * np.sqrt(G_CGS * m_star_g / r_cm)

    omega_k = np.sqrt(G_CGS * m_star_g / r_cm**3)

    # beta (Eq. 14)
    x = r_au / characteristic_radius
    beta = gamma + (2.0 - gamma) * x ** (2.0 - gamma)

    # da/dt (Eq. 13)
    coeff = c_mig_i * (2.7 + 1.1 * beta)
    da_dt_cgs = (
        -coeff * (m_total_g / m_star_g) * (sigma_g * r_cm**2 / m_star_g) * (r_cm * omega_k / cs) ** 2 * (r_cm * omega_k)
    )

    # Convert cm/s to AU/yr
    return float(da_dt_cgs / AU_CM * (365.25 * 24 * 3600))


def type_ii_migration_rate(
    embryo: Embryo,
    sigma_g: float,
    stellar_mass: float,
    gas_dissipation_timescale: float,
) -> float:
    """Type II migration rate da/dt (Eq. 15).

    Applies when the planet is massive enough to open a gap.

    Parameters
    ----------
    embryo : Embryo
        Current embryo state.
    sigma_g : float
        Local gas surface density in g/cm^2.
    stellar_mass : float
        Stellar mass in solar masses.
    gas_dissipation_timescale : float
        Gas depletion timescale in years.

    Returns
    -------
    float
        Migration rate in AU/year (negative = inward).
    """
    r_au = embryo.semi_major_axis
    r_cm = r_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    m_total_g = embryo.total_mass * M_EARTH_G

    h_over_r = _disk_aspect_ratio(r_au, stellar_mass)

    alpha = 1e-3  # viscosity parameter
    omega_k = np.sqrt(G_CGS * m_star_g / r_cm**3)

    # Migration radius R_m (Eq. 16)
    tau_disc_s = gas_dissipation_timescale * 365.25 * 24 * 3600
    r_m_cm = 10.0 * np.exp(-2.0 * tau_disc_s / (3.0 * tau_disc_s)) * AU_CM
    # Simplified: use local viscous drift
    sign = -1.0 if r_au > r_m_cm / AU_CM else 1.0

    da_dt_cgs = (
        sign
        * 3.0
        * alpha
        * (sigma_g * r_cm**2 / m_star_g)
        * (omega_k / (m_total_g / m_star_g))
        * h_over_r**2
        * r_cm
        * omega_k
    )

    return float(da_dt_cgs / AU_CM * (365.25 * 24 * 3600))


def gap_opening_mass_earth(r_au: float, stellar_mass: float) -> float:
    """Minimum mass to open a gap (transition Type I -> Type II).

    Parameters
    ----------
    r_au : float
        Semi-major axis in AU.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Gap-opening mass in Earth masses.
    """
    h_over_r = _disk_aspect_ratio(r_au, stellar_mass)
    # Thermal criterion: M_gap ~ M* * (h/r)^3
    m_gap_g = stellar_mass * M_SUN_G * h_over_r**3
    return m_gap_g / M_EARTH_G


def migration_rate(
    embryo: Embryo,
    sigma_g: float,
    disk_params_stellar_mass: float,
    disk_params_characteristic_radius: float,
    disk_params_gas_dissipation_timescale: float,
    config_gamma: float,
    config_c_mig_i: float,
) -> float:
    """Compute the appropriate migration rate for an embryo.

    Selects Type I or Type II based on gap-opening criterion.

    Parameters
    ----------
    embryo : Embryo
        Current embryo state.
    sigma_g : float
        Local gas surface density in g/cm^2.
    disk_params_stellar_mass : float
        Stellar mass in solar masses.
    disk_params_characteristic_radius : float
        Characteristic radius a_c in AU.
    disk_params_gas_dissipation_timescale : float
        Gas depletion timescale in years.
    config_gamma : float
        Density profile exponent.
    config_c_mig_i : float
        Type I migration delay factor.

    Returns
    -------
    float
        Migration rate in AU/year.
    """
    m_gap = gap_opening_mass_earth(embryo.semi_major_axis, disk_params_stellar_mass)

    if embryo.total_mass < m_gap:
        return type_i_migration_rate(
            embryo,
            sigma_g,
            disk_params_stellar_mass,
            config_gamma,
            disk_params_characteristic_radius,
            config_c_mig_i,
        )
    return type_ii_migration_rate(
        embryo,
        sigma_g,
        disk_params_stellar_mass,
        disk_params_gas_dissipation_timescale,
    )
