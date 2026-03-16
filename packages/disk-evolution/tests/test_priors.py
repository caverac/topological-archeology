"""Tests for prior sampling module."""

from unittest.mock import patch

import numpy as np
import pytest
from disk_evolution.models import DiskParams, ModelConfig
from disk_evolution.priors import _draw_unchecked, draw_disk_params, draw_population


def test_draw_unchecked_returns_disk_params() -> None:
    """_draw_unchecked returns a DiskParams."""
    rng = np.random.default_rng(42)
    params = _draw_unchecked(rng)
    assert isinstance(params, DiskParams)


def test_draw_unchecked_ranges() -> None:
    """Drawn values are in physically reasonable ranges."""
    rng = np.random.default_rng(42)
    params = _draw_unchecked(rng)
    assert 0.3 < params.stellar_mass < 3.0
    assert params.disk_mass > 0
    assert params.characteristic_radius > 0
    assert -2.0 < params.metallicity < 2.0
    assert 1e5 < params.gas_dissipation_timescale < 1e8


def test_draw_disk_params_stable() -> None:
    """draw_disk_params returns a stable disk."""
    rng = np.random.default_rng(42)
    config = ModelConfig(gamma=1.0)
    params = draw_disk_params(rng, config)
    assert params.disk_mass <= 0.2 * params.stellar_mass


def test_draw_population_count() -> None:
    """draw_population returns the requested number of systems."""
    config = ModelConfig(gamma=1.0)
    pop = draw_population(5, config, seed=0)
    assert len(pop) == 5
    assert all(isinstance(p, DiskParams) for p in pop)


def test_draw_disk_params_raises_on_max_attempts() -> None:
    """Raise RuntimeError when no stable disk found after max_attempts."""
    rng = np.random.default_rng(42)
    unstable = DiskParams(
        stellar_mass=0.7, disk_mass=0.5, characteristic_radius=10.0, metallicity=0.0, gas_dissipation_timescale=1e6
    )
    config = ModelConfig(gamma=1.0)
    with patch("disk_evolution.priors._draw_unchecked", return_value=unstable):
        with pytest.raises(RuntimeError, match="No stable disk"):
            draw_disk_params(rng, config, max_attempts=3)


def test_draw_population_reproducible() -> None:
    """Same seed gives same results."""
    config = ModelConfig(gamma=1.0)
    pop1 = draw_population(3, config, seed=123)
    pop2 = draw_population(3, config, seed=123)
    for p1, p2 in zip(pop1, pop2):
        assert p1.stellar_mass == p2.stellar_mass
