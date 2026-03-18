"""Planetesimal eccentricity and inclination evolution.

Gravitational stirring from Ohtsuki et al. (2002) and gas drag
damping from Adachi et al. (1976), following Guilera et al. (2010)
Eqs. 19-27.
"""

from __future__ import annotations

import numpy as np
from disk_evolution.models import AU_CM, G_CGS, K_BOLTZ, M_EARTH_G, M_PROTON, M_SUN_G

# ---------------------------------------------------------------------------
# Gas drag coefficient
# ---------------------------------------------------------------------------

C_D: float = 1.0
"""Dimensionless drag coefficient for spherical bodies."""

RHO_PLANETESIMAL: float = 1.5
"""Mean density of planetesimals in g/cm^3."""

R_PLANETESIMAL_CM: float = 1e5
"""Default planetesimal radius: 1 km = 1e5 cm."""


def _planetesimal_mass_g() -> float:
    """Mass of a single planetesimal.

    Returns
    -------
    float
        Mass in grams.
    """
    return (4.0 / 3.0) * np.pi * R_PLANETESIMAL_CM**3 * RHO_PLANETESIMAL


# ---------------------------------------------------------------------------
# Viscous stirring coefficients (Ohtsuki et al. 2002; Guilera Eqs. 19-24)
# ---------------------------------------------------------------------------


def _i_pvs(beta: float) -> float:
    """Approximate I_PVS(beta) for viscous stirring (Chambers fit).

    Parameters
    ----------
    beta : float
        Ratio i_hat / e_hat.

    Returns
    -------
    float
        I_PVS value.
    """
    beta = max(beta, 1e-6)
    return float((beta - 0.36251) / (0.061547 + 0.16112 * beta + 0.054473 * beta**2))


def _q_pvs(beta: float) -> float:
    """Approximate Q_PVS(beta) for viscous stirring (Chambers fit).

    Parameters
    ----------
    beta : float
        Ratio i_hat / e_hat.

    Returns
    -------
    float
        Q_PVS value.
    """
    beta = max(beta, 1e-6)
    return float((0.71946 - beta) / (0.21239 + 0.49764 * beta + 0.14369 * beta**2))


def viscous_stirring(
    m_planet_g: float,
    m_star_g: float,
    r_hill: float,
    ecc: float,
    inc: float,
    a_cm: float,
    period: float,
) -> tuple[float, float]:
    """Compute gravitational stirring rates for e^2 and i^2.

    Parameters
    ----------
    m_planet_g : float
        Planet mass in grams.
    m_star_g : float
        Stellar mass in grams.
    r_hill : float
        Hill radius in cm.
    ecc : float
        RMS eccentricity of planetesimals.
    inc : float
        RMS inclination of planetesimals (radians).
    a_cm : float
        Semi-major axis in cm.
    period : float
        Orbital period in seconds.

    Returns
    -------
    tuple[float, float]
        (de^2/dt, di^2/dt) in 1/s.
    """
    e_hat = max(ecc * a_cm / r_hill, 1e-6)
    i_hat = max(inc * a_cm / r_hill, 1e-6)
    beta = i_hat / e_hat

    lambda_sq = i_hat * (i_hat**2 + e_hat**2) / 12.0
    lambda_sq = max(lambda_sq, 1e-12)

    # P_VS (Guilera Eq. 19)
    term1 = (73.0 * e_hat**2 / (10.0 * lambda_sq)) * np.log(1.0 + 10.0 * lambda_sq / e_hat**2)
    term2 = (72.0 * _i_pvs(beta) / (np.pi * e_hat * i_hat)) * np.log(1.0 + lambda_sq)
    p_vs = term1 + term2

    # Q_VS (Guilera Eq. 20)
    term3_num = 4.0 * i_hat**2 + 0.2 * i_hat * e_hat**3
    term3 = (term3_num / (10.0 * lambda_sq * e_hat)) * np.log(1.0 + 10.0 * lambda_sq)
    term4 = (72.0 * _q_pvs(beta) / (np.pi * e_hat * i_hat)) * np.log(1.0 + lambda_sq)
    q_vs = term3 + term4

    # b = mutual Hill radius parameter ~ 1 (in units of Hill radii)
    b = 1.0
    prefactor = m_planet_g / (3.0 * b * m_star_g * period)

    return float(prefactor * p_vs), float(prefactor * q_vs)


# ---------------------------------------------------------------------------
# Gas drag damping (Adachi et al. 1976; Guilera Eqs. 26-27)
# ---------------------------------------------------------------------------


def _eta_headwind(a_au: float, stellar_mass: float, gamma: float) -> float:
    """Ratio of sub-Keplerian gas velocity to Keplerian velocity.

    Parameters
    ----------
    a_au : float
        Semi-major axis in AU.
    stellar_mass : float
        Stellar mass in solar masses.
    gamma : float
        Disk density profile exponent.

    Returns
    -------
    float
        eta = (v_K - v_gas) / v_K.
    """
    # Temperature profile: T ~ 280 * (r/AU)^{-0.5} * (L/L_sun)^{0.25}
    luminosity = stellar_mass**4.0
    temp = 280.0 * (a_au ** (-0.5)) * luminosity**0.25
    mu = 2.34
    cs_sq = K_BOLTZ * temp / (mu * M_PROTON)
    a_cm = a_au * AU_CM
    v_k_sq = G_CGS * stellar_mass * M_SUN_G / a_cm

    # eta ~ (pi/16) * (alpha + beta_T) * (cs/vk)^2
    # alpha = gamma (surface density exponent), beta_T ~ 0.5 (temperature exponent)
    beta_t = 0.5
    return float((np.pi / 16.0) * (gamma + beta_t) * cs_sq / v_k_sq)


def gas_drag_damping(
    ecc: float,
    inc: float,
    a_au: float,
    rho_gas: float,
    stellar_mass: float,
    gamma: float,
) -> tuple[float, float]:
    """Compute gas drag damping rates for e and i.

    Parameters
    ----------
    ecc : float
        RMS eccentricity.
    inc : float
        RMS inclination (radians).
    a_au : float
        Semi-major axis in AU.
    rho_gas : float
        Midplane gas density in g/cm^3.
    stellar_mass : float
        Stellar mass in solar masses.
    gamma : float
        Disk density profile exponent.

    Returns
    -------
    tuple[float, float]
        (de/dt, di/dt) in 1/s. Both are negative (damping).
    """
    a_cm = a_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    v_k = np.sqrt(G_CGS * m_star_g / a_cm)
    m_p = _planetesimal_mass_g()

    eta = _eta_headwind(a_au, stellar_mass, gamma)
    v_rel_sq = (5.0 / 8.0) * ecc**2 + 0.5 * inc**2

    common = np.pi * R_PLANETESIMAL_CM**2 * C_D * rho_gas * v_k / m_p
    drag_factor = common * (eta**2 + v_rel_sq)

    de_dt = -ecc * drag_factor / 2.0
    di_dt = -inc * drag_factor / 4.0

    return float(de_dt), float(di_dt)


def _sigma_to_rho_midplane(sigma_g: float, a_au: float, stellar_mass: float) -> float:
    """Convert gas surface density to midplane volume density.

    Parameters
    ----------
    sigma_g : float
        Gas surface density in g/cm^2.
    a_au : float
        Semi-major axis in AU.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Midplane gas density in g/cm^3.
    """
    # rho_mid = Sigma_g / (sqrt(2*pi) * H)
    # H/r ~ cs / v_K
    a_cm = a_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    luminosity = stellar_mass**4.0
    temp = 280.0 * (a_au ** (-0.5)) * luminosity**0.25
    mu = 2.34
    cs = np.sqrt(K_BOLTZ * temp / (mu * M_PROTON))
    v_k = np.sqrt(G_CGS * m_star_g / a_cm)
    h_over_r = cs / v_k
    h_cm = h_over_r * a_cm

    return float(sigma_g / (np.sqrt(2.0 * np.pi) * h_cm))


def evolve_eccentricity_inclination(
    ecc: float,
    inc: float,
    m_planet_earth: float,
    a_au: float,
    sigma_g: float,
    stellar_mass: float,
    gamma: float,
    dt_yr: float,
) -> tuple[float, float]:
    """Evolve eccentricity and inclination for one timestep.

    Combines gravitational stirring and gas drag damping.

    Parameters
    ----------
    ecc : float
        Current RMS eccentricity.
    inc : float
        Current RMS inclination (radians).
    m_planet_earth : float
        Planet mass in Earth masses.
    a_au : float
        Semi-major axis in AU.
    sigma_g : float
        Local gas surface density in g/cm^2.
    stellar_mass : float
        Stellar mass in solar masses.
    gamma : float
        Disk density profile exponent.
    dt_yr : float
        Timestep in years.

    Returns
    -------
    tuple[float, float]
        Updated (eccentricity, inclination).
    """
    a_cm = a_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    m_planet_g = m_planet_earth * M_EARTH_G
    dt_s = dt_yr * 365.25 * 24.0 * 3600.0

    r_hill = a_cm * (m_planet_g / (3.0 * m_star_g)) ** (1.0 / 3.0)
    omega = np.sqrt(G_CGS * m_star_g / a_cm**3)
    period = 2.0 * np.pi / omega

    # Stirring (de^2/dt, di^2/dt)
    de2_dt_stir, di2_dt_stir = viscous_stirring(m_planet_g, m_star_g, r_hill, ecc, inc, a_cm, period)

    # Gas drag (de/dt, di/dt)
    rho_gas = _sigma_to_rho_midplane(sigma_g, a_au, stellar_mass)
    de_dt_drag, di_dt_drag = gas_drag_damping(ecc, inc, a_au, rho_gas, stellar_mass, gamma)

    # Update e^2 and i^2
    e_sq = ecc**2 + de2_dt_stir * dt_s + 2.0 * ecc * de_dt_drag * dt_s
    i_sq = inc**2 + di2_dt_stir * dt_s + 2.0 * inc * di_dt_drag * dt_s

    # Floor to prevent negative values
    new_ecc = float(np.sqrt(max(e_sq, 1e-12)))
    new_inc = float(np.sqrt(max(i_sq, 1e-12)))

    return new_ecc, new_inc
