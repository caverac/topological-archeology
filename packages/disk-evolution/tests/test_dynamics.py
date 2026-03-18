"""Tests for planetesimal eccentricity and inclination evolution."""

import numpy as np
from disk_evolution.dynamics import (
    _eta_headwind,
    _i_pvs,
    _planetesimal_mass_g,
    _q_pvs,
    _sigma_to_rho_midplane,
    evolve_eccentricity_inclination,
    gas_drag_damping,
    viscous_stirring,
)
from disk_evolution.models import AU_CM, G_CGS, M_EARTH_G, M_SUN_G


def test_planetesimal_mass_positive() -> None:
    """Verify planetesimal mass is positive and reasonable."""
    m = _planetesimal_mass_g()
    assert m > 0
    # 1 km body at 1.5 g/cm^3 ~ 6e15 g
    assert 1e14 < m < 1e17


def test_i_pvs_returns_float() -> None:
    """Verify I_PVS returns a finite value."""
    val = _i_pvs(0.5)
    assert np.isfinite(val)


def test_q_pvs_returns_float() -> None:
    """Verify Q_PVS returns a finite value."""
    val = _q_pvs(0.5)
    assert np.isfinite(val)


def test_viscous_stirring_positive() -> None:
    """Verify stirring rates are positive (stirring increases e, i)."""
    m_planet_g = 1.0 * M_EARTH_G
    m_star_g = 1.0 * M_SUN_G
    a_cm = 5.0 * AU_CM
    r_hill = a_cm * (m_planet_g / (3.0 * m_star_g)) ** (1.0 / 3.0)
    omega = np.sqrt(G_CGS * m_star_g / a_cm**3)
    period = 2.0 * np.pi / omega

    de2_dt, di2_dt = viscous_stirring(m_planet_g, m_star_g, r_hill, 0.01, 0.005, a_cm, period)
    assert de2_dt > 0
    assert di2_dt > 0


def test_gas_drag_damping_negative() -> None:
    """Verify gas drag decreases eccentricity and inclination."""
    de_dt, di_dt = gas_drag_damping(ecc=0.01, inc=0.005, a_au=5.0, rho_gas=1e-10, stellar_mass=1.0, gamma=1.0)
    assert de_dt < 0
    assert di_dt < 0


def test_eta_headwind_positive() -> None:
    """Verify sub-Keplerian headwind is positive."""
    eta = _eta_headwind(5.0, 1.0, 1.0)
    assert eta > 0
    # eta ~ 10^{-3} for typical disks
    assert 1e-5 < eta < 1e-1


def test_sigma_to_rho_midplane_positive() -> None:
    """Verify midplane density conversion is positive."""
    rho = _sigma_to_rho_midplane(100.0, 5.0, 1.0)
    assert rho > 0


def test_evolve_eccentricity_inclination_damped() -> None:
    """Verify e, i decrease with strong gas drag (no planet stirring)."""
    # Tiny planet (low stirring), dense gas (strong damping)
    ecc_new, inc_new = evolve_eccentricity_inclination(
        ecc=0.1,
        inc=0.05,
        m_planet_earth=0.001,
        a_au=5.0,
        sigma_g=1000.0,
        stellar_mass=1.0,
        gamma=1.0,
        dt_yr=1e4,
    )
    assert ecc_new < 0.1
    assert inc_new < 0.05


def test_evolve_eccentricity_inclination_stirred() -> None:
    """Verify e, i increase with massive planet (strong stirring) and no gas."""
    # Massive planet, very low gas density
    ecc_new, inc_new = evolve_eccentricity_inclination(
        ecc=1e-4,
        inc=5e-5,
        m_planet_earth=100.0,
        a_au=5.0,
        sigma_g=0.01,
        stellar_mass=1.0,
        gamma=1.0,
        dt_yr=1e4,
    )
    assert ecc_new > 1e-4
    assert inc_new > 5e-5


def test_evolve_eccentricity_floors_at_small_values() -> None:
    """Verify eccentricity and inclination don't go negative."""
    ecc_new, inc_new = evolve_eccentricity_inclination(
        ecc=1e-10,
        inc=1e-10,
        m_planet_earth=0.01,
        a_au=5.0,
        sigma_g=100.0,
        stellar_mass=1.0,
        gamma=1.0,
        dt_yr=1e4,
    )
    assert ecc_new > 0
    assert inc_new > 0
