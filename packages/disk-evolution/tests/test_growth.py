"""Tests for embryo growth module."""

from disk_evolution.growth import (
    critical_mass_earth,
    gas_accretion_rate,
    kelvin_helmholtz_timescale_yr,
    oligarchic_mass_earth,
    solid_accretion_rate,
)
from disk_evolution.models import Embryo


def test_oligarchic_mass_positive() -> None:
    """Oligarchic onset mass is positive for nonzero surface density."""
    m = oligarchic_mass_earth(sigma_s=10.0, r_au=1.0, stellar_mass=1.0)
    assert m > 0


def test_solid_accretion_rate_zero_sigma() -> None:
    """No solid accretion when surface density is zero."""
    e = Embryo(semi_major_axis=1.0, core_mass=1.0)
    rate = solid_accretion_rate(e, sigma_s=0.0, stellar_mass=1.0)
    assert rate == 0.0


def test_solid_accretion_rate_positive() -> None:
    """Positive accretion rate for nonzero conditions."""
    e = Embryo(semi_major_axis=1.0, core_mass=1.0)
    rate = solid_accretion_rate(e, sigma_s=10.0, stellar_mass=1.0)
    assert rate > 0


def test_critical_mass() -> None:
    """Critical mass scales with accretion rate."""
    m1 = critical_mass_earth(1e-7)
    m2 = critical_mass_earth(1e-5)
    assert m2 > m1
    # At typical rate 1e-6, M_crit ~ 10 M_earth
    m_typical = critical_mass_earth(1e-6)
    assert 9.0 < m_typical < 11.0


def test_kh_timescale_decreasing() -> None:
    """More massive planets have shorter KH timescales."""
    t1 = kelvin_helmholtz_timescale_yr(1.0)
    t10 = kelvin_helmholtz_timescale_yr(10.0)
    assert t10 < t1


def test_gas_accretion_below_critical() -> None:
    """No gas accretion when below critical mass."""
    e = Embryo(semi_major_axis=1.0, core_mass=0.001)
    rate = gas_accretion_rate(e, core_accretion_rate_val=1e-6)
    assert rate == 0.0


def test_gas_accretion_above_critical() -> None:
    """Gas accretion starts when core exceeds critical mass."""
    # Core of 20 M_earth with low accretion rate -> M_crit ~ 10 -> triggers gas accretion
    e = Embryo(semi_major_axis=1.0, core_mass=20.0, envelope_mass=5.0)
    rate = gas_accretion_rate(e, core_accretion_rate_val=1e-6)
    assert rate > 0
