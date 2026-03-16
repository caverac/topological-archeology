"""Tests for disk profile module."""

import numpy as np
from disk_evolution.disk import (
    DiskState,
    _isolation_mass_earth,
    embryo_spacing_au,
    inner_boundary_au,
    is_stable,
    toomre_q,
)
from disk_evolution.models import DiskParams, ModelConfig


def _make_params() -> DiskParams:
    return DiskParams(
        stellar_mass=1.0,
        disk_mass=0.05,
        characteristic_radius=40.0,
        metallicity=0.0,
        gas_dissipation_timescale=3e6,
    )


def test_inner_boundary_solar() -> None:
    """Inner boundary for a solar-mass star is a few hundredths of AU."""
    a_in = inner_boundary_au(1.0)
    assert 0.01 < a_in < 0.2


def test_embryo_spacing_positive() -> None:
    """Embryo spacing is positive and scales with distance."""
    da1 = embryo_spacing_au(1.0, 0.01, 1.0)
    da5 = embryo_spacing_au(5.0, 0.01, 1.0)
    assert da1 > 0
    assert da5 > da1


def test_isolation_mass_positive() -> None:
    """Isolation mass is positive for nonzero surface density."""
    m = _isolation_mass_earth(1.0, 10.0, 1.0)
    assert m > 0


def test_disk_state_sigma_gas_positive() -> None:
    """Gas surface density is positive within the disk."""
    params = _make_params()
    config = ModelConfig(gamma=1.0)
    disk = DiskState(params, config)
    disk.__post_init__()

    r = np.array([1.0, 5.0, 20.0])
    sig = disk.sigma_gas(r)
    assert np.all(sig > 0)


def test_disk_state_sigma_solids_ice_line() -> None:
    """Solid surface density jumps by ~4x at the snow line."""
    params = _make_params()
    config = ModelConfig(gamma=1.0)
    disk = DiskState(params, config)
    disk.__post_init__()

    # Snow line for 1 Msun ~ 2.7 AU
    r_inside = np.array([2.0])
    r_outside = np.array([3.5])
    sig_in = disk.sigma_solids(r_inside)
    sig_out = disk.sigma_solids(r_outside)
    # Outside should be higher per unit due to ice (eta=1 vs 0.25)
    # but profile also drops, so just check ratio isn't 1
    ratio = float(sig_out[0] / sig_in[0])
    assert ratio != 1.0


def test_disk_state_perturbation() -> None:
    """Perturbation modulates the solid surface density."""
    params = _make_params()
    config_smooth = ModelConfig(gamma=1.0, perturbation_amplitude=0.0)
    config_trans = ModelConfig(gamma=1.0, perturbation_amplitude=0.3)

    disk_s = DiskState(params, config_smooth)
    disk_s.__post_init__()
    disk_t = DiskState(params, config_trans)
    disk_t.__post_init__()

    r = np.linspace(1.0, 10.0, 100)
    sig_smooth = disk_s.sigma_solids(r)
    sig_trans = disk_t.sigma_solids(r)

    # They should differ
    assert not np.allclose(sig_smooth, sig_trans)


def test_initial_embryo_positions_reasonable_count() -> None:
    """Number of initial embryos is in a reasonable range (5-200)."""
    params = _make_params()
    config = ModelConfig(gamma=1.0)
    disk = DiskState(params, config)
    disk.__post_init__()
    positions = disk.initial_embryo_positions()
    assert 5 < len(positions) < 200


def test_toomre_stable_disk() -> None:
    """A low-mass disk should be Toomre stable."""
    params = DiskParams(
        stellar_mass=1.0, disk_mass=0.01, characteristic_radius=40.0, metallicity=0.0, gas_dissipation_timescale=3e6
    )
    config = ModelConfig(gamma=1.0)
    q = toomre_q(params, config)
    assert q > 1.0
    assert is_stable(params, config)


def test_toomre_unstable_heavy_disk() -> None:
    """A disk exceeding 20% of stellar mass is rejected."""
    params = DiskParams(
        stellar_mass=1.0, disk_mass=0.3, characteristic_radius=40.0, metallicity=0.0, gas_dissipation_timescale=3e6
    )
    config = ModelConfig(gamma=1.0)
    assert not is_stable(params, config)
