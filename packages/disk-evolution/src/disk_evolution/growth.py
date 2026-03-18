"""Embryo growth: solid accretion and gas accretion.

Solid accretion uses the Inaba et al. (2001) three-regime collision
probability following Guilera, Brunini & Benvenuto (2010) Eqs. 8-15.

Gas accretion uses the Kelvin-Helmholtz contraction prescription
from Ida & Lin (2004a) Eqs. 21-23.
"""

from __future__ import annotations

import numpy as np
from disk_evolution.models import AU_CM, G_CGS, M_EARTH_G, M_SUN_G, YR_S, Embryo

# ---------------------------------------------------------------------------
# Physical radius of a rocky body
# ---------------------------------------------------------------------------

RHO_CORE: float = 5.5
"""Mean density of a rocky embryo in g/cm^3."""

SEED_MASS_EARTH: float = 0.01
"""Default initial embryo mass in Earth masses (Fortier 2013, Sec. 5.1)."""


def _physical_radius_cm(mass_g: float) -> float:
    """Physical radius of a uniform-density rocky body.

    Parameters
    ----------
    mass_g : float
        Body mass in grams.

    Returns
    -------
    float
        Radius in cm.
    """
    return float((3.0 * mass_g / (4.0 * np.pi * RHO_CORE)) ** (1.0 / 3.0))


# ---------------------------------------------------------------------------
# Collision probability (Inaba et al. 2001; Guilera 2010 Eqs. 9-11, 13)
# ---------------------------------------------------------------------------


def _i_f(beta: float) -> float:
    """Approximate I_F(beta) for collision probability (Chambers fit).

    Parameters
    ----------
    beta : float
        Ratio i_hat / e_hat (reduced inclination / reduced eccentricity).

    Returns
    -------
    float
        I_F value.
    """
    beta = max(beta, 1e-6)
    return float((1.0 + 0.95925 * beta + 0.77251 * beta**2) / (beta * (0.13142 + 0.12295 * beta)))


def _i_g(beta: float) -> float:
    """Approximate I_G(beta) for collision probability (Chambers fit).

    Parameters
    ----------
    beta : float
        Ratio i_hat / e_hat.

    Returns
    -------
    float
        I_G value.
    """
    beta = max(beta, 1e-6)
    return float((1.0 + 0.39960 * beta) / (beta * (0.0369 + 0.048333 * beta + 0.006874 * beta**2)))


def _collision_probability(
    r_capture: float,
    r_hill: float,
    e_hat: float,
    i_hat: float,
) -> float:
    """Three-regime collision probability (Guilera 2010 Eqs. 9-11, 13).

    Parameters
    ----------
    r_capture : float
        Capture radius (physical or enhanced) in cm.
    r_hill : float
        Hill radius in cm.
    e_hat : float
        Reduced eccentricity (e * a / R_H).
    i_hat : float
        Reduced inclination (i * a / R_H).

    Returns
    -------
    float
        Collision probability P_coll (dimensionless).
    """
    e_hat = max(e_hat, 1e-6)
    i_hat = max(i_hat, 1e-6)
    beta = i_hat / e_hat

    rc_rh = r_capture / r_hill
    rc_rh_sq = rc_rh**2

    # High-velocity regime (e_hat, i_hat > 2)
    p_high = (rc_rh_sq / (2.0 * np.pi)) * (_i_f(beta) + 6.0 * _i_g(beta) / (rc_rh_sq * e_hat**2))

    # Medium-velocity regime (0.2 < e_hat, i_hat < 2)
    p_med = (rc_rh_sq / (4.0 * np.pi * i_hat)) * (17.3 + 232.0 / rc_rh)

    # Low-velocity regime (e_hat, i_hat < 0.2)
    p_low = 11.3 * rc_rh**0.5

    # Combined (Inaba et al. 2001)
    p_high_low = 0.0
    if p_low > 0 and p_high > 0:
        p_high_low = (p_low ** (-2) + p_high ** (-2)) ** (-0.5)

    return float(min(p_med, p_high_low) if p_high_low > 0 else p_med)


# ---------------------------------------------------------------------------
# Solid accretion rate (Guilera 2010 Eq. 8)
# ---------------------------------------------------------------------------


def solid_accretion_rate(
    embryo: Embryo,
    sigma_s: float,
    stellar_mass: float,
) -> float:
    """Rate of solid accretion dM_s/dt using particle-in-a-box.

    Uses the Inaba et al. (2001) collision probability with three
    velocity regimes, following Guilera et al. (2010) Eq. 8.

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

    # Hill radius
    r_hill = r_cm * (m_total_g / (3.0 * m_star_g)) ** (1.0 / 3.0)

    # Physical (capture) radius -- no envelope enhancement for now
    r_capture = _physical_radius_cm(m_total_g)

    # Orbital period
    omega = np.sqrt(G_CGS * m_star_g / r_cm**3)
    period = 2.0 * np.pi / omega

    # Equilibrium eccentricity and inclination (oligarchic regime)
    # e ~ (M / M*)^{1/3}, i ~ e/2 (Ida & Makino 1993)
    ecc = max(float((m_total_g / m_star_g) ** (1.0 / 3.0)), 1e-8)
    inc = ecc / 2.0

    # Reduced eccentricity and inclination
    e_hat = ecc * r_cm / r_hill
    i_hat = inc * r_cm / r_hill

    # Collision probability
    p_coll = _collision_probability(r_capture, r_hill, e_hat, i_hat)

    # dM/dt = 2*pi * Sigma * R_H^2 / P * P_coll (Guilera Eq. 8)
    dm_dt_cgs = 2.0 * np.pi * sigma_s * r_hill**2 / period * p_coll

    return float(dm_dt_cgs / M_EARTH_G * YR_S)


# ---------------------------------------------------------------------------
# Gas accretion (Ida & Lin 2004a, Eqs. 21-23)
# ---------------------------------------------------------------------------


def critical_mass_earth(core_accretion_rate: float) -> float:
    """Critical core mass for runaway gas accretion.

    From Ida & Lin (2004a) Eq. 22 / Miguel (2011) Eq. 10.

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
    rate = max(abs(core_accretion_rate), 1e-10)
    return float(10.0 * (rate / 1e-6) ** 0.25)


def kelvin_helmholtz_timescale_yr(total_mass_earth: float) -> float:
    """Kelvin-Helmholtz contraction timescale.

    Uses the Ida & Lin (2004a) Eq. 21 prescription:
    tau_KH = 10^b * (M / M_earth)^{-c} with b=9, c=3.

    Parameters
    ----------
    total_mass_earth : float
        Total embryo mass in Earth masses.

    Returns
    -------
    float
        KH timescale in years.
    """
    # Ida & Lin (2004a) Eq. 21: tau_KH = 10^9 * (M/M_earth)^{-3} yr
    return float(1e9 * total_mass_earth ** (-3.0))


def gas_accretion_rate(embryo: Embryo, core_accretion_rate_val: float = 1e-6) -> float:
    """Rate of gas envelope accretion dM_g/dt.

    Gas accretion begins when core mass exceeds M_crit.
    Rate is M_total / tau_KH (Ida & Lin 2004a, Eq. 23).

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

    # dM_g/dt = M_total / tau_KH (Ida & Lin 2004a Eq. 23)
    return float(embryo.total_mass / tau_kh)
