"""Tests for persistent homology computation."""

import numpy as np
from topo_archeo.persistence import (
    CONSOLIDATED_LABELS,
    PersistenceResult,
    _preprocess,
    compute_persistence,
)


def _make_clustered_cloud() -> np.ndarray:
    """Create a point cloud with two well-separated clusters."""
    rng = np.random.default_rng(42)
    cluster_a = rng.normal(loc=0.0, scale=0.1, size=(50, 6))
    cluster_b = rng.normal(loc=5.0, scale=0.1, size=(50, 6))
    return np.vstack([cluster_a, cluster_b])


def _make_loop_cloud() -> np.ndarray:
    """Create a point cloud shaped like a circle (should have H1)."""
    theta = np.linspace(0, 2 * np.pi, 100, endpoint=False)
    x = np.cos(theta)
    y = np.sin(theta)
    return np.column_stack([x, y])


def test_compute_persistence_returns_result() -> None:
    """Verify compute_persistence returns a PersistenceResult."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud)
    assert isinstance(result, PersistenceResult)
    assert len(result.diagrams) == 2  # H0 and H1


def test_h0_detects_two_clusters() -> None:
    """Verify H0 detects two clusters in well-separated data."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud, max_dim=0)
    lt = result.lifetimes(0)
    assert len(lt) > 0
    assert lt[0] > 1.0


def test_h0_property() -> None:
    """Verify h0 property returns the H0 diagram."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud, max_dim=1)
    assert result.h0 is result.diagrams[0]


def test_h1_property() -> None:
    """Verify h1 property returns the H1 diagram."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud, max_dim=1)
    assert result.h1 is result.diagrams[1]


def test_h1_detects_loop() -> None:
    """Verify H1 detects a loop in circular data."""
    cloud = _make_loop_cloud()
    result = compute_persistence(cloud, max_dim=1, labels=["x", "y"], log_transform=False)
    lt = result.lifetimes(1)
    assert len(lt) > 0
    assert lt[0] > 0.5


def test_n_persistent_features() -> None:
    """Verify n_persistent_features counts correctly."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud)
    n = result.n_persistent_features(0, threshold=1.0)
    assert n >= 1


def test_lifetimes_sorted_descending() -> None:
    """Verify lifetimes are sorted in descending order."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud)
    lt = result.lifetimes(0)
    assert len(lt) > 1
    assert all(lt[i] >= lt[i + 1] for i in range(len(lt) - 1))


def test_scaling_changes_result() -> None:
    """Verify scaling affects the persistence diagrams."""
    cloud = _make_clustered_cloud()
    r_scaled = compute_persistence(cloud, scale=True)
    r_unscaled = compute_persistence(cloud, scale=False)
    assert r_scaled.lifetimes(0)[0] != r_unscaled.lifetimes(0)[0]


def test_default_labels_for_6d() -> None:
    """Verify default labels are CONSOLIDATED_LABELS for 6D data."""
    cloud = _make_clustered_cloud()
    result = compute_persistence(cloud)
    assert result.labels == CONSOLIDATED_LABELS


def test_custom_labels() -> None:
    """Verify custom labels are used when provided."""
    cloud = _make_loop_cloud()
    result = compute_persistence(cloud, labels=["a", "b"], log_transform=False)
    assert result.labels == ["a", "b"]


def test_auto_labels_non_6d() -> None:
    """Verify auto-generated labels for non-6D data."""
    cloud = _make_loop_cloud()
    result = compute_persistence(cloud, log_transform=False)
    assert result.labels == ["x0", "x1"]


def test_log_transform_reduces_skewness() -> None:
    """Verify log1p transform reduces skewness of heavy-tailed features."""
    rng = np.random.default_rng(42)
    # Create a 6D cloud where columns 2,3,4 are log-normal
    cloud = rng.normal(size=(100, 6))
    cloud[:, 2] = np.exp(cloud[:, 2] * 2)  # heavy right skew
    cloud[:, 3] = np.exp(cloud[:, 3] * 3)
    cloud[:, 4] = np.exp(cloud[:, 4] * 2)

    raw = _preprocess(cloud, log_transform=False, scale=True)
    logged = _preprocess(cloud, log_transform=True, scale=True)

    # After log transform, the max values should be less extreme
    assert float(np.max(np.abs(logged[:, 2]))) < float(np.max(np.abs(raw[:, 2])))
    assert float(np.max(np.abs(logged[:, 3]))) < float(np.max(np.abs(raw[:, 3])))


def test_log_transform_skipped_for_non_6d() -> None:
    """Verify log transform is not applied to non-6D data."""
    cloud = _make_loop_cloud()
    raw = _preprocess(cloud, log_transform=True, scale=False)
    no_log = _preprocess(cloud, log_transform=False, scale=False)
    # For 2D data, log_transform=True should have no effect
    np.testing.assert_array_equal(raw, no_log)


def test_no_log_transform_option() -> None:
    """Verify log_transform=False skips the transform."""
    cloud = _make_clustered_cloud()
    r_log = compute_persistence(cloud, log_transform=True)
    r_nolog = compute_persistence(cloud, log_transform=False)
    # Different preprocessing should give different results
    assert r_log.lifetimes(0)[0] != r_nolog.lifetimes(0)[0]
