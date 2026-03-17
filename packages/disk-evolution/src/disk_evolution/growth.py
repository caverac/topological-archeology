"""Embryo growth: solid accretion and gas accretion.

Implements Eqs. 8-12 from Miguel et al. (2011).
"""

from __future__ import annotations

import numpy as np
from disk_evolution.models import AU_CM, G_CGS, M_EARTH_G, M_SUN_G, YR_S, Embryo

# ---------------------------------------------------------------------------
# Oligarchic growth regime (solid accretion)
# ---------------------------------------------------------------------------


def oligarchic_mass_earth(
    sigma_s: float,
    r_au: float,
    stellar_mass: float,
) -> float:
    """Onset mass for oligarchic growth regime (Eq. 8, Ida & Makino 1993).

    Parameters
    ----------
    sigma_s : float
        Local solid surface density in g/cm^2.
    r_au : float
        Semi-major axis in AU.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Oligarchic onset mass in Earth masses.
    """
    r_cm = r_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    # Effective planetesimal mass (assume m ~ 1e18 g, km-sized)
    m_eff = 1e18
    numerator = 1.6 * r_cm ** (6.0 / 5.0) * m_eff ** (2.0 / 5.0) * sigma_s ** (3.0 / 5.0)
    denominator = m_star_g ** (1.0 / 5.0)
    return float(numerator / denominator / M_EARTH_G)


def solid_accretion_rate(
    embryo: Embryo,
    sigma_s: float,
    stellar_mass: float,
) -> float:
    """Rate of solid accretion dM_s/dt (Eq. 9).

    Parameters
    ----------
    embryo : Embryo
        Current embryo state.
    sigma_s : float
        Local solid surface density in g/cm^2.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Accretion rate in Earth masses per year.
    """
    if sigma_s <= 0.0:
        return 0.0

    r_cm = embryo.semi_major_axis * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    m_total_g = embryo.total_mass * M_EARTH_G

    # Kepler frequency
    omega = np.sqrt(G_CGS * m_star_g / r_cm**3)

    # Physical radius of the embryo (rocky body, rho ~ 5.5 g/cm^3)
    rho_core = 5.5
    r_phys = (3.0 * m_total_g / (4.0 * np.pi * rho_core)) ** (1.0 / 3.0)

    # Velocity dispersion of planetesimals: sigma ~ e * v_K
    # Eccentricity equilibrium: e ~ (M / M*)^{1/3} in oligarchic regime
    v_k = omega * r_cm
    ecc = (m_total_g / m_star_g) ** (1.0 / 3.0)
    sigma_v = max(ecc * v_k, 1.0)  # floor to avoid division by zero

    # Eq. 9: dM_s/dt = 10.33 * Sigma_s * Omega * R_p^2 * (1 + 2GM / (R_p * sigma^2))
    grav_focus = 1.0 + 2.0 * G_CGS * m_total_g / (r_phys * sigma_v**2)
    dm_dt_cgs = 10.33 * sigma_s * omega * r_phys**2 * grav_focus

    return float(dm_dt_cgs / M_EARTH_G * YR_S)


# ---------------------------------------------------------------------------
# Gas accretion
# ---------------------------------------------------------------------------


def critical_mass_earth(core_accretion_rate: float) -> float:
    """Critical core mass for runaway gas accretion (Eq. 10).

    Parameters
    ----------
    core_accretion_rate : float
        Solid accretion rate dM_c/dt in M_earth/yr.

    Returns
    -------
    float
        Critical mass in Earth masses.
    """
    # M_crit ~ 10 * (dM_c/dt / 1e-6 M_earth/yr)^{1/4}
    # Typical values: dM_c/dt ~ 1e-6 -> M_crit ~ 10 M_earth
    rate = max(abs(core_accretion_rate), 1e-10)
    return float(10.0 * (rate / 1e-6) ** 0.25)


def kelvin_helmholtz_timescale_yr(total_mass_earth: float) -> float:
    """Kelvin-Helmholtz contraction timescale tau_g (Eq. 12).

    Parameters
    ----------
    total_mass_earth : float
        Total embryo mass in Earth masses.

    Returns
    -------
    float
        KH timescale in years.
    """
    return float(8.35e10 * total_mass_earth ** (-4.89))


def gas_accretion_rate(embryo: Embryo, core_accretion_rate_val: float = 1e-6) -> float:
    """Rate of gas envelope accretion dM_g/dt (Eq. 11).

    Gas accretion begins when core mass exceeds M_crit.
    Rate is M_envelope / tau_KH.

    Parameters
    ----------
    embryo : Embryo
        Current embryo state.
    core_accretion_rate_val : float
        Current solid accretion rate in M_earth/yr (for M_crit calculation).

    Returns
    -------
    float
        Gas accretion rate in Earth masses per year.
    """
    m_crit = critical_mass_earth(core_accretion_rate_val)
    if embryo.core_mass < m_crit:
        return 0.0

    tau_kh = kelvin_helmholtz_timescale_yr(embryo.total_mass)
    if tau_kh <= 0.0:  # pragma: no cover
        return 0.0

    # dM_g/dt = M_envelope / tau_KH
    return max(embryo.envelope_mass, 0.01) / tau_kh
