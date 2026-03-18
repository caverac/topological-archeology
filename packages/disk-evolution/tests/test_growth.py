"""Tests for embryo growth module."""

from disk_evolution.growth import (
    _collision_probability,
    _i_f,
    _i_g,
    _physical_radius_cm,
    critical_mass_earth,
    gas_accretion_rate,
    kelvin_helmholtz_timescale_yr,
    solid_accretion_rate,
)
from disk_evolution.models import Embryo


def test_physical_radius_positive() -> None:
    """Physical radius is positive for nonzero mass."""
    r = _physical_radius_cm(5.972e27)  # 1 M_earth
    assert r > 0
    # Earth radius ~ 6.4e8 cm
    assert 5e8 < r < 8e8


def test_i_f_positive() -> None:
    """Verify I_F is positive for valid beta."""
    assert _i_f(0.5) > 0
    assert _i_f(1.0) > 0


def test_i_g_positive() -> None:
    """Verify I_G is positive for valid beta."""
    assert _i_g(0.5) > 0
    assert _i_g(1.0) > 0


def test_collision_probability_three_regimes() -> None:
    """Verify collision probability is positive across velocity regimes."""
    # High velocity (e_hat, i_hat > 2)
    p_high = _collision_probability(1e8, 1e12, 5.0, 2.5)
    assert p_high > 0

    # Medium velocity (0.2 < e_hat, i_hat < 2)
    p_med = _collision_probability(1e8, 1e12, 1.0, 0.5)
    assert p_med > 0

    # Low velocity (e_hat, i_hat < 0.2)
    p_low = _collision_probability(1e8, 1e12, 0.1, 0.05)
    assert p_low > 0


def test_collision_probability_larger_capture_gives_higher() -> None:
    """Larger capture radius gives higher collision probability."""
    p_small = _collision_probability(1e8, 1e12, 1.0, 0.5)
    p_large = _collision_probability(1e9, 1e12, 1.0, 0.5)
    assert p_large > p_small


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


def test_solid_accretion_rate_order_of_magnitude() -> None:
    """Accretion rate is in the expected range (~1e-6 to 1e-4 Me/yr)."""
    e = Embryo(semi_major_axis=3.0, core_mass=0.1)
    rate = solid_accretion_rate(e, sigma_s=8.0, stellar_mass=1.0)
    assert 1e-8 < rate < 1e-2


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


def test_kh_timescale_ida_lin() -> None:
    """Verify KH timescale matches Ida & Lin (2004a) Eq. 21."""
    # tau_KH = 10^9 * (M/M_earth)^{-3}
    # At 10 M_earth: 10^9 / 1000 = 10^6 yr
    tau = kelvin_helmholtz_timescale_yr(10.0)
    assert abs(tau - 1e6) < 1e3


def test_gas_accretion_below_critical() -> None:
    """No gas accretion when below critical mass."""
    e = Embryo(semi_major_axis=1.0, core_mass=0.001)
    rate = gas_accretion_rate(e, core_accretion_rate_val=1e-6)
    assert rate == 0.0


def test_gas_accretion_above_critical() -> None:
    """Gas accretion starts when core exceeds critical mass."""
    # Core of 20 M_earth with low accretion rate -> M_crit ~ 10 -> triggers
    e = Embryo(semi_major_axis=1.0, core_mass=20.0, envelope_mass=5.0)
    rate = gas_accretion_rate(e, core_accretion_rate_val=1e-6)
    assert rate > 0


def test_gas_accretion_uses_total_mass() -> None:
    """Gas accretion rate uses M_total / tau_KH, not M_envelope / tau_KH."""
    e = Embryo(semi_major_axis=1.0, core_mass=20.0, envelope_mass=5.0)
    rate = gas_accretion_rate(e, core_accretion_rate_val=1e-6)
    tau = kelvin_helmholtz_timescale_yr(25.0)
    expected = 25.0 / tau
    assert abs(rate - expected) < 1e-10
