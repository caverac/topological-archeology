"""Data models for disk evolution simulation input and output."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

# ---------------------------------------------------------------------------
# Physical constants (CGS unless noted)
# ---------------------------------------------------------------------------

M_SUN_G: float = 1.989e33
"""Solar mass in grams."""

M_EARTH_G: float = 5.972e27
"""Earth mass in grams."""

AU_CM: float = 1.496e13
"""Astronomical unit in cm."""

G_CGS: float = 6.674e-8
"""Gravitational constant in CGS."""

YR_S: float = 3.156e7
"""Year in seconds."""

L_SUN_CGS: float = 3.828e33
"""Solar luminosity in erg/s."""

K_BOLTZ: float = 1.381e-16
"""Boltzmann constant in CGS."""

M_PROTON: float = 1.673e-24
"""Proton mass in grams."""

T_SUB: float = 1500.0
"""Dust sublimation temperature in Kelvin."""


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiskParams:
    """Initial conditions for a single protoplanetary disk.

    Parameters
    ----------
    stellar_mass : float
        Stellar mass in solar masses. Range: [0.7, 1.4].
    disk_mass : float
        Total disk mass in solar masses.
    characteristic_radius : float
        Characteristic radius a_c in AU.
    metallicity : float
        Stellar metallicity [Fe/H].
    gas_dissipation_timescale : float
        Timescale for gas depletion in years. Range: [1e6, 1e7].
    """

    stellar_mass: float
    disk_mass: float
    characteristic_radius: float
    metallicity: float
    gas_dissipation_timescale: float


@dataclass(frozen=True)
class ModelConfig:
    """Fixed model parameters for a simulation run.

    Parameters
    ----------
    gamma : float
        Density profile exponent for the inner disk. One of {0.5, 1.0, 1.5}.
    c_mig_i : float
        Type I migration delay factor. 0 = no migration, 0.01, 0.1, or 1.0.
    perturbation_amplitude : float
        Disk density perturbation amplitude A. 0 = smooth, 0.3 = transitional.
    perturbation_length_scale : float
        Length scale f for the density perturbation (Chaparro Eq. 1.1).
    total_time : float
        Total integration time in years.
    dt : float
        Timestep in years.
    """

    gamma: float = 1.0
    c_mig_i: float = 0.1
    perturbation_amplitude: float = 0.0
    perturbation_length_scale: float = 1.0
    total_time: float = 2.0e7
    dt: float = 1.0e4


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


@dataclass
class Embryo:
    """State of a single planetary embryo during simulation.

    Parameters
    ----------
    semi_major_axis : float
        Current orbital semi-major axis in AU.
    core_mass : float
        Solid core mass in Earth masses.
    envelope_mass : float
        Gas envelope mass in Earth masses.
    alive : bool
        Whether the embryo is still active (not merged or ejected).
    """

    semi_major_axis: float
    core_mass: float
    envelope_mass: float = 0.0
    alive: bool = True

    @property
    def total_mass(self) -> float:
        """Total mass (core + envelope) in Earth masses."""
        return self.core_mass + self.envelope_mass

    @property
    def is_giant(self) -> bool:
        """Whether the planet is a giant (total mass > 15 M_earth)."""
        return self.total_mass > 15.0


@dataclass(frozen=True)
class Planet:
    """Final state of a planet after simulation completes.

    Parameters
    ----------
    semi_major_axis : float
        Final orbital semi-major axis in AU.
    total_mass : float
        Total mass (solid + gas) in Earth masses.
    core_mass : float
        Solid core mass in Earth masses.
    """

    semi_major_axis: float
    total_mass: float
    core_mass: float

    @property
    def is_giant(self) -> bool:
        """Whether the planet is a giant (total mass > 15 M_earth)."""
        return self.total_mass > 15.0


@dataclass(frozen=True)
class SystemArchitecture:
    """Raw output of a single simulation: the list of formed planets.

    Parameters
    ----------
    planets : tuple[Planet, ...]
        Tuple of planets formed in the system.
    disk_params : DiskParams
        The initial conditions that produced this system.
    """

    planets: tuple[Planet, ...]
    disk_params: DiskParams


@dataclass(frozen=True)
class ConsolidatedOutput:
    """Consolidated summary quantities for a planetary system.

    This is the fixed-length feature vector used for TDA analysis.

    Parameters
    ----------
    n_giant : int
        Number of giant planets (M > 15 M_earth).
    n_terrestrial : int
        Number of terrestrial planets (M <= 15 M_earth).
    total_terrestrial_mass : float
        Sum of terrestrial planet masses in M_earth.
    avg_terrestrial_mass : float
        Mean terrestrial planet mass in M_earth (0 if none).
    mass_efficiency : float
        Total planet mass / disk mass ratio (dimensionless).
    center_of_mass : float
        First moment of mass distribution w.r.t. semi-major axis (AU).
    """

    n_giant: int
    n_terrestrial: int
    total_terrestrial_mass: float
    avg_terrestrial_mass: float
    mass_efficiency: float
    center_of_mass: float

    def to_array(self) -> npt.NDArray[np.float64]:
        """Convert to a numpy array for TDA input.

        Returns
        -------
        npt.NDArray[np.float64]
            Array of shape (6,) with the consolidated quantities.
        """
        return np.array(
            [
                float(self.n_giant),
                float(self.n_terrestrial),
                self.total_terrestrial_mass,
                self.avg_terrestrial_mass,
                self.mass_efficiency,
                self.center_of_mass,
            ],
            dtype=np.float64,
        )


def consolidate(architecture: SystemArchitecture) -> ConsolidatedOutput:
    """Compute consolidated quantities from a system architecture.

    Parameters
    ----------
    architecture : SystemArchitecture
        The raw simulation output.

    Returns
    -------
    ConsolidatedOutput
        Fixed-length summary vector.
    """
    planets = architecture.planets
    disk_mass_earth = architecture.disk_params.disk_mass * (M_SUN_G / M_EARTH_G)

    giants = [p for p in planets if p.is_giant]
    terrestrials = [p for p in planets if not p.is_giant]

    n_giant = len(giants)
    n_terrestrial = len(terrestrials)

    total_terrestrial_mass = sum(p.total_mass for p in terrestrials)
    avg_terrestrial_mass = total_terrestrial_mass / n_terrestrial if n_terrestrial > 0 else 0.0

    total_planet_mass = sum(p.total_mass for p in planets)
    mass_efficiency = total_planet_mass / disk_mass_earth if disk_mass_earth > 0 else 0.0

    if total_planet_mass > 0:
        center_of_mass = sum(p.total_mass * p.semi_major_axis for p in planets) / total_planet_mass
    else:
        center_of_mass = 0.0

    return ConsolidatedOutput(
        n_giant=n_giant,
        n_terrestrial=n_terrestrial,
        total_terrestrial_mass=total_terrestrial_mass,
        avg_terrestrial_mass=avg_terrestrial_mass,
        mass_efficiency=mass_efficiency,
        center_of_mass=center_of_mass,
    )


# ---------------------------------------------------------------------------
# Batch output
# ---------------------------------------------------------------------------


@dataclass
class PopulationResult:
    """Result of a population synthesis run (many systems).

    Parameters
    ----------
    architectures : list[SystemArchitecture]
        Raw outputs for each simulated system.
    consolidated : list[ConsolidatedOutput]
        Consolidated summaries, one per system.
    config : ModelConfig
        The model configuration used.
    """

    architectures: list[SystemArchitecture] = field(default_factory=list)
    consolidated: list[ConsolidatedOutput] = field(default_factory=list)
    config: ModelConfig = field(default_factory=ModelConfig)

    def to_point_cloud(self) -> npt.NDArray[np.float64]:
        """Stack consolidated outputs into a (N, 6) array for TDA.

        Returns
        -------
        npt.NDArray[np.float64]
            Array of shape (N, 6).
        """
        return np.stack([c.to_array() for c in self.consolidated])
