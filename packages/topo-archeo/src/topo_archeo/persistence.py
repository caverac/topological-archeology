"""Persistent homology computation for planetary architecture point clouds.

Computes Vietoris-Rips persistence on the consolidated output space
to detect formation channels (H0) and degeneracies (H1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from ripser import ripser  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]


@dataclass(frozen=True)
class PersistenceResult:
    """Result of a persistent homology computation.

    Parameters
    ----------
    diagrams : list[npt.NDArray[np.float64]]
        Persistence diagrams for each homology dimension.
        Each array has shape (n_features, 2) with (birth, death) pairs.
    point_cloud : npt.NDArray[np.float64]
        The (scaled) point cloud used for computation.
    labels : list[str]
        Feature labels for the point cloud columns.
    """

    diagrams: list[npt.NDArray[np.float64]]
    point_cloud: npt.NDArray[np.float64]
    labels: list[str]

    @property
    def h0(self) -> npt.NDArray[np.float64]:
        """Return H0 (connected components) persistence diagram."""
        return self.diagrams[0]

    @property
    def h1(self) -> npt.NDArray[np.float64]:
        """Return H1 (loops) persistence diagram."""
        return self.diagrams[1]

    def lifetimes(self, dim: int) -> npt.NDArray[np.float64]:
        """Compute persistence lifetimes for a given homology dimension.

        Parameters
        ----------
        dim : int
            Homology dimension (0 or 1).

        Returns
        -------
        npt.NDArray[np.float64]
            Array of lifetimes, sorted descending.
        """
        dgm = self.diagrams[dim]
        finite_mask = np.isfinite(dgm[:, 1])
        lifetimes: npt.NDArray[np.float64] = dgm[finite_mask, 1] - dgm[finite_mask, 0]
        return np.sort(lifetimes)[::-1]

    def n_persistent_features(self, dim: int, threshold: float) -> int:
        """Count features with lifetime above a threshold.

        Parameters
        ----------
        dim : int
            Homology dimension.
        threshold : float
            Minimum lifetime to count as significant.

        Returns
        -------
        int
            Number of persistent features.
        """
        lt = self.lifetimes(dim)
        return int(np.sum(lt > threshold))


CONSOLIDATED_LABELS: list[str] = [
    "n_giant",
    "n_terrestrial",
    "total_terrestrial_mass",
    "avg_terrestrial_mass",
    "mass_efficiency",
    "center_of_mass",
]


def compute_persistence(
    point_cloud: npt.NDArray[np.float64],
    max_dim: int = 1,
    scale: bool = True,
    labels: list[str] | None = None,
) -> PersistenceResult:
    """Compute Vietoris-Rips persistent homology on a point cloud.

    Parameters
    ----------
    point_cloud : npt.NDArray[np.float64]
        Array of shape (N, D) with N points in D dimensions.
    max_dim : int
        Maximum homology dimension to compute. Default 1 (H0 and H1).
    scale : bool
        Whether to standardize features before computing persistence.
    labels : list[str] | None
        Feature labels. Defaults to CONSOLIDATED_LABELS if D=6.

    Returns
    -------
    PersistenceResult
        Persistence diagrams and metadata.
    """
    if labels is None:
        if point_cloud.shape[1] == len(CONSOLIDATED_LABELS):
            labels = CONSOLIDATED_LABELS
        else:
            labels = [f"x{i}" for i in range(point_cloud.shape[1])]

    if scale:
        scaler = StandardScaler()
        scaled: npt.NDArray[np.float64] = scaler.fit_transform(point_cloud)
    else:
        scaled = point_cloud.copy()

    result = ripser(scaled, maxdim=max_dim)
    diagrams: list[npt.NDArray[np.float64]] = [np.array(dgm, dtype=np.float64) for dgm in result["dgms"]]

    return PersistenceResult(
        diagrams=diagrams,
        point_cloud=scaled,
        labels=labels,
    )
