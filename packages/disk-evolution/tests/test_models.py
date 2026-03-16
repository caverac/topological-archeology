"""Tests for data models and consolidation."""

import numpy as np
from disk_evolution.models import (
    ConsolidatedOutput,
    DiskParams,
    Embryo,
    ModelConfig,
    Planet,
    PopulationResult,
    SystemArchitecture,
    consolidate,
)


def _make_disk_params() -> DiskParams:
    return DiskParams(
        stellar_mass=1.0,
        disk_mass=0.01,
        characteristic_radius=30.0,
        metallicity=0.0,
        gas_dissipation_timescale=3e6,
    )


def test_embryo_total_mass() -> None:
    """Embryo total mass is core + envelope."""
    e = Embryo(semi_major_axis=1.0, core_mass=5.0, envelope_mass=3.0)
    assert e.total_mass == 8.0


def test_embryo_is_giant() -> None:
    """Giant threshold is 15 M_earth."""
    assert not Embryo(semi_major_axis=1.0, core_mass=10.0).is_giant
    assert Embryo(semi_major_axis=1.0, core_mass=10.0, envelope_mass=6.0).is_giant


def test_planet_is_giant() -> None:
    """Planet giant threshold matches embryo."""
    assert not Planet(semi_major_axis=1.0, total_mass=14.9, core_mass=10.0).is_giant
    assert Planet(semi_major_axis=1.0, total_mass=15.1, core_mass=10.0).is_giant


def test_consolidate_empty_system() -> None:
    """Empty system gives zero consolidated output."""
    arch = SystemArchitecture(planets=(), disk_params=_make_disk_params())
    c = consolidate(arch)
    assert c.n_giant == 0
    assert c.n_terrestrial == 0
    assert c.center_of_mass == 0.0


def test_consolidate_mixed_system() -> None:
    """Consolidation correctly separates giants and terrestrials."""
    planets = (
        Planet(semi_major_axis=0.5, total_mass=1.0, core_mass=1.0),
        Planet(semi_major_axis=1.0, total_mass=5.0, core_mass=5.0),
        Planet(semi_major_axis=5.0, total_mass=300.0, core_mass=10.0),
    )
    arch = SystemArchitecture(planets=planets, disk_params=_make_disk_params())
    c = consolidate(arch)

    assert c.n_giant == 1
    assert c.n_terrestrial == 2
    assert c.total_terrestrial_mass == 6.0
    assert c.avg_terrestrial_mass == 3.0
    assert c.mass_efficiency > 0.0
    # CoM = (1*0.5 + 5*1.0 + 300*5.0) / 306 ~ 4.92
    assert 4.5 < c.center_of_mass < 5.0


def test_consolidated_to_array() -> None:
    """to_array returns shape (6,) float64."""
    c = ConsolidatedOutput(
        n_giant=1,
        n_terrestrial=2,
        total_terrestrial_mass=6.0,
        avg_terrestrial_mass=3.0,
        mass_efficiency=0.1,
        center_of_mass=2.0,
    )
    arr = c.to_array()
    assert arr.shape == (6,)
    assert arr.dtype == np.float64


def test_population_result_to_point_cloud() -> None:
    """Verify PopulationResult stacks consolidated outputs."""
    c1 = ConsolidatedOutput(
        n_giant=0,
        n_terrestrial=3,
        total_terrestrial_mass=3.0,
        avg_terrestrial_mass=1.0,
        mass_efficiency=0.01,
        center_of_mass=1.0,
    )
    c2 = ConsolidatedOutput(
        n_giant=1,
        n_terrestrial=1,
        total_terrestrial_mass=2.0,
        avg_terrestrial_mass=2.0,
        mass_efficiency=0.05,
        center_of_mass=3.0,
    )
    pop = PopulationResult(consolidated=[c1, c2])
    cloud = pop.to_point_cloud()
    assert cloud.shape == (2, 6)


def test_model_config_defaults() -> None:
    """Verify ModelConfig has sensible defaults."""
    cfg = ModelConfig()
    assert cfg.gamma == 1.0
    assert cfg.total_time == 2.0e7
    assert cfg.dt == 1.0e4
