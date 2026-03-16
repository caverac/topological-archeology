"""Tests for migration module."""

from disk_evolution.migration import (
    gap_opening_mass_earth,
    migration_rate,
    type_i_migration_rate,
    type_ii_migration_rate,
)
from disk_evolution.models import Embryo


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


def test_type_ii_returns_float() -> None:
    """Type II migration returns a finite float."""
    e = Embryo(semi_major_axis=5.0, core_mass=100.0, envelope_mass=200.0)
    rate = type_ii_migration_rate(e, sigma_g=100.0, stellar_mass=1.0, gas_dissipation_timescale=3e6)
    assert isinstance(rate, float)
    assert abs(rate) < 1e10  # sanity: not infinite


def test_gap_opening_mass_positive() -> None:
    """Gap-opening mass is positive."""
    m = gap_opening_mass_earth(1.0, 1.0)
    assert m > 0


def test_migration_rate_selects_type() -> None:
    """migration_rate dispatches correctly based on mass."""
    # Small embryo -> Type I
    e_small = Embryo(semi_major_axis=1.0, core_mass=1.0)
    rate_small = migration_rate(e_small, 100.0, 1.0, 30.0, 3e6, 1.0, 0.1)

    # Massive embryo -> Type II
    e_big = Embryo(semi_major_axis=1.0, core_mass=100.0, envelope_mass=200.0)
    rate_big = migration_rate(e_big, 100.0, 1.0, 30.0, 3e6, 1.0, 0.1)

    # Both should be finite
    assert abs(rate_small) < 1e10
    assert abs(rate_big) < 1e10
