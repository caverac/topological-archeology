"""Planetary migration: Type I and Type II.

Type I uses the Tanaka et al. (2002) formula with a delay factor
c_mig_i that can reduce or disable migration.

Type II follows Ida & Lin (2004a) Eqs. 50-54 with time-evolving R_m
and quantities evaluated at R_m.

Gap opening uses the Crida et al. (2006) combined thermal + viscous criterion.
"""

from __future__ import annotations

import numpy as np
from disk_evolution.models import AU_CM, G_CGS, K_BOLTZ, M_EARTH_G, M_PROTON, M_SUN_G, Embryo

# Viscosity parameter (Shakura-Sunyaev)
ALPHA_VISC: float = 1e-3


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
    """Type I migration rate da/dt (Tanaka et al. 2002 / Miguel Eq. 13).

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

    # beta (Eq. 14): local surface density slope
    x = r_au / characteristic_radius
    beta = gamma + (2.0 - gamma) * x ** (2.0 - gamma)

    # da/dt (Eq. 13)
    coeff = c_mig_i * (2.7 + 1.1 * beta)
    da_dt_cgs = (
        -coeff * (m_total_g / m_star_g) * (sigma_g * r_cm**2 / m_star_g) * (r_cm * omega_k / cs) ** 2 * (r_cm * omega_k)
    )

    return float(da_dt_cgs / AU_CM * (365.25 * 24 * 3600))


def _r_m_au(t_yr: float, gas_dissipation_timescale: float) -> float:
    """Maximum viscous couple radius R_m (Ida & Lin 2004a Eq. 54).

    Parameters
    ----------
    t_yr : float
        Current time in years.
    gas_dissipation_timescale : float
        Gas depletion timescale in years.

    Returns
    -------
    float
        R_m in AU.
    """
    return float(10.0 * np.exp(2.0 * t_yr / (5.0 * gas_dissipation_timescale)))


def type_ii_migration_rate(
    embryo: Embryo,
    sigma_g: float,
    stellar_mass: float,
    gas_dissipation_timescale: float,
    t_yr: float,
) -> float:
    """Type II migration rate da/dt (Ida & Lin 2004a Eq. 50).

    Quantities evaluated at R_m per Ida & Lin prescription.

    Parameters
    ----------
    embryo : Embryo
        Current embryo state.
    sigma_g : float
        Local gas surface density in g/cm^2 (used to estimate Sigma at R_m).
    stellar_mass : float
        Stellar mass in solar masses.
    gas_dissipation_timescale : float
        Gas depletion timescale in years.
    t_yr : float
        Current simulation time in years.

    Returns
    -------
    float
        Migration rate in AU/year.
    """
    r_au = embryo.semi_major_axis
    r_cm = r_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    m_total_g = embryo.total_mass * M_EARTH_G

    # R_m evolves with time (Ida & Lin Eq. 54)
    r_m = _r_m_au(t_yr, gas_dissipation_timescale)
    r_m_cm = r_m * AU_CM

    # Evaluate quantities at R_m
    h_over_r_m = _disk_aspect_ratio(r_m, stellar_mass)
    omega_k_m = np.sqrt(G_CGS * m_star_g / r_m_cm**3)
    omega_k_p = np.sqrt(G_CGS * m_star_g / r_cm**3)

    # Estimate Sigma_g at R_m from local value using power-law scaling
    sigma_g_m = sigma_g * (r_m / r_au) ** (-1.5)  # approximate MMSN scaling

    sign = -1.0 if r_au < r_m else 1.0

    # da/dt / a = 3 * sign * alpha * Sigma_m * R_m^2 / M_p * Omega_m / Omega_p * (h_m/a_p)^2 * Omega_m
    rate = (
        sign
        * 3.0
        * ALPHA_VISC
        * (sigma_g_m * r_m_cm**2 / m_total_g)
        * (omega_k_m / omega_k_p)
        * (h_over_r_m * r_m_cm / r_cm) ** 2
        * omega_k_m
    )

    # da/dt = rate * a_p
    da_dt_cgs = rate * r_cm

    return float(da_dt_cgs / AU_CM * (365.25 * 24 * 3600))


def gap_opening_mass_earth(r_au: float, stellar_mass: float) -> float:
    """Minimum mass to open a gap using Crida et al. (2006) criterion.

    Combines thermal and viscous conditions:
    (3/4)(H/R_H) + 50/(q*Re) <= 1
    where q = M_p/M*, Re = a^2*Omega/(alpha*cs*H).

    Simplified: M_gap ~ max(thermal, viscous).

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
    m_star_g = stellar_mass * M_SUN_G

    # Thermal criterion: M_gap,th ~ M* * (h/r)^3
    m_th = m_star_g * h_over_r**3

    # Viscous criterion: M_gap,vis ~ 40 * alpha * M* * (h/r)^2
    # From Crida: 50/(q*Re) = 1 => q = 50/(Re) => M_p = 50*alpha*cs*H*M*/(a^2*Omega)
    # Simplifies to ~ 50*alpha*(h/r)^2 * M*
    m_vis = 50.0 * ALPHA_VISC * h_over_r**2 * m_star_g

    return float(max(m_th, m_vis) / M_EARTH_G)


def migration_rate(
    embryo: Embryo,
    sigma_g: float,
    disk_params_stellar_mass: float,
    disk_params_characteristic_radius: float,
    disk_params_gas_dissipation_timescale: float,
    config_gamma: float,
    config_c_mig_i: float,
    t_yr: float = 0.0,
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
    t_yr : float
        Current simulation time in years.

    Returns
    -------
    float
        Migration rate in AU/year.
    """
    # c_mig_i = 0 disables ALL migration (both Type I and Type II)
    if config_c_mig_i == 0.0:
        return 0.0

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
        t_yr,
    )
