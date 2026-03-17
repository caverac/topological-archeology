"""Tests for planetary system classification."""

from disk_evolution.classify import SystemType, classify
from disk_evolution.models import DiskParams, Planet, SystemArchitecture


def _dp() -> DiskParams:
    return DiskParams(
        stellar_mass=1.0,
        disk_mass=0.05,
        characteristic_radius=30.0,
        metallicity=0.0,
        gas_dissipation_timescale=3e6,
    )


def test_failed_no_planets() -> None:
    """Empty system is classified as failed."""
    arch = SystemArchitecture(planets=(), disk_params=_dp())
    assert classify(arch) == SystemType.FAILED


def test_failed_below_mercury() -> None:
    """System with only sub-Mercury planets is failed."""
    planets = (Planet(semi_major_axis=1.0, total_mass=0.01, core_mass=0.01),)
    arch = SystemArchitecture(planets=planets, disk_params=_dp())
    assert classify(arch) == SystemType.FAILED


def test_low_mass_only_terrestrials() -> None:
    """System with only terrestrial planets is low mass."""
    planets = (
        Planet(semi_major_axis=1.0, total_mass=1.0, core_mass=1.0),
        Planet(semi_major_axis=3.0, total_mass=5.0, core_mass=5.0),
    )
    arch = SystemArchitecture(planets=planets, disk_params=_dp())
    assert classify(arch) == SystemType.LOW_MASS


def test_hot_warm_jupiter() -> None:
    """Giant inside 1 AU with no giants between 1-30 AU."""
    planets = (
        Planet(semi_major_axis=0.05, total_mass=300.0, core_mass=10.0),
        Planet(semi_major_axis=2.0, total_mass=5.0, core_mass=5.0),
    )
    arch = SystemArchitecture(planets=planets, disk_params=_dp())
    assert classify(arch) == SystemType.HOT_WARM_JUPITER


def test_solar_system() -> None:
    """Giants between 1-30 AU with none inside 1 AU."""
    planets = (
        Planet(semi_major_axis=5.0, total_mass=318.0, core_mass=10.0),
        Planet(semi_major_axis=10.0, total_mass=95.0, core_mass=10.0),
        Planet(semi_major_axis=0.5, total_mass=1.0, core_mass=1.0),
    )
    arch = SystemArchitecture(planets=planets, disk_params=_dp())
    assert classify(arch) == SystemType.SOLAR


def test_combined() -> None:
    """Giants both inside 1 AU and between 1-30 AU."""
    planets = (
        Planet(semi_major_axis=0.05, total_mass=300.0, core_mass=10.0),
        Planet(semi_major_axis=5.0, total_mass=100.0, core_mass=10.0),
    )
    arch = SystemArchitecture(planets=planets, disk_params=_dp())
    assert classify(arch) == SystemType.COMBINED


def test_cold_jupiter() -> None:
    """Giants only beyond 30 AU."""
    planets = (
        Planet(semi_major_axis=50.0, total_mass=100.0, core_mass=10.0),
        Planet(semi_major_axis=1.0, total_mass=1.0, core_mass=1.0),
    )
    arch = SystemArchitecture(planets=planets, disk_params=_dp())
    assert classify(arch) == SystemType.COLD_JUPITER
