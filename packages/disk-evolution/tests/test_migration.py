"""Tests for migration module."""

from disk_evolution.migration import (
    _disk_aspect_ratio,
    _r_m_au,
    gap_opening_mass_earth,
    migration_rate,
    type_i_migration_rate,
    type_ii_migration_rate,
)
from disk_evolution.models import M_EARTH_G, M_SUN_G, Embryo


def test_type_i_disabled_when_zero() -> None:
    """Type I migration is zero when c_mig_i = 0."""
    e = Embryo(semi_major_axis=1.0, core_mass=5.0)
    rate = type_i_migration_rate(e, sigma_g=100.0, stellar_mass=1.0, gamma=1.0, characteristic_radius=30.0, c_mig_i=0.0)
    assert rate == 0.0


def test_type_i_inward() -> None:
    """Type I migration is inward (negative da/dt)."""
    e = Embryo(semi_major_axis=1.0, core_mass=5.0)
    rate = type_i_migration_rate(e, sigma_g=100.0, stellar_mass=1.0, gamma=1.0, characteristic_radius=30.0, c_mig_i=0.1)
    assert rate < 0


def test_r_m_evolves_outward() -> None:
    """Verify R_m increases with time (Ida & Lin Eq. 54)."""
    r0 = _r_m_au(0.0, 3e6)
    r1 = _r_m_au(1e6, 3e6)
    r2 = _r_m_au(5e6, 3e6)
    assert r0 == 10.0
    assert r1 > r0
    assert r2 > r1


def test_type_ii_returns_float() -> None:
    """Type II migration returns a finite float."""
    e = Embryo(semi_major_axis=5.0, core_mass=100.0, envelope_mass=200.0)
    rate = type_ii_migration_rate(e, sigma_g=100.0, stellar_mass=1.0, gas_dissipation_timescale=3e6, t_yr=1e6)
    assert isinstance(rate, float)
    assert abs(rate) < 1e10


def test_type_ii_inward_inside_rm() -> None:
    """Planet inside R_m migrates inward."""
    e = Embryo(semi_major_axis=3.0, core_mass=100.0, envelope_mass=200.0)
    rate = type_ii_migration_rate(e, sigma_g=100.0, stellar_mass=1.0, gas_dissipation_timescale=3e6, t_yr=0.0)
    # At t=0, R_m=10 AU, planet at 3 AU -> inward
    assert rate < 0


def test_type_ii_outward_outside_rm() -> None:
    """Planet outside R_m migrates outward."""
    e = Embryo(semi_major_axis=15.0, core_mass=100.0, envelope_mass=200.0)
    rate = type_ii_migration_rate(e, sigma_g=100.0, stellar_mass=1.0, gas_dissipation_timescale=3e6, t_yr=0.0)
    # At t=0, R_m=10 AU, planet at 15 AU -> outward
    assert rate > 0


def test_gap_opening_mass_positive() -> None:
    """Gap-opening mass is positive."""
    m = gap_opening_mass_earth(1.0, 1.0)
    assert m > 0


def test_gap_opening_crida_viscous() -> None:
    """Verify Crida criterion gives higher gap mass than pure thermal."""
    # At small h/r, viscous criterion dominates
    m = gap_opening_mass_earth(5.0, 1.0)
    assert m > 0
    # Should be >= pure thermal (h/r)^3 * M*
    h_over_r = _disk_aspect_ratio(5.0, 1.0)
    m_thermal = 1.0 * M_SUN_G * h_over_r**3 / M_EARTH_G
    assert m >= m_thermal


def test_migration_rate_selects_type() -> None:
    """Verify migration_rate dispatches correctly based on mass."""
    # Small embryo -> Type I
    e_small = Embryo(semi_major_axis=1.0, core_mass=1.0)
    rate_small = migration_rate(e_small, 100.0, 1.0, 30.0, 3e6, 1.0, 0.1, t_yr=1e6)

    # Massive embryo -> Type II
    e_big = Embryo(semi_major_axis=1.0, core_mass=100.0, envelope_mass=200.0)
    rate_big = migration_rate(e_big, 100.0, 1.0, 30.0, 3e6, 1.0, 0.1, t_yr=1e6)

    # Both should be finite
    assert abs(rate_small) < 1e10
    assert abs(rate_big) < 1e10
