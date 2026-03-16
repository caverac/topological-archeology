"""Protoplanetary disk surface density profiles and initial embryo placement.

Implements the disk model from Miguel et al. (2011), Eqs. 1-7,
with the density perturbation from Chaparro Molano et al. (2019), Eq. 1.1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from disk_evolution.models import AU_CM, G_CGS, K_BOLTZ, M_EARTH_G, M_PROTON, M_SUN_G, T_SUB, DiskParams, ModelConfig

# ---------------------------------------------------------------------------
# Primordial abundance
# ---------------------------------------------------------------------------

Z_0: float = 0.0149
"""Primordial solar heavy-element abundance (Lodders 2003)."""


# ---------------------------------------------------------------------------
# DiskState: precomputed, cacheable disk representation
# ---------------------------------------------------------------------------


@dataclass
class DiskState:
    """Precomputed disk state for fast evaluation during simulation.

    All expensive normalization integrals are computed once at construction.

    Parameters
    ----------
    disk_params : DiskParams
        Disk initial conditions.
    config : ModelConfig
        Model configuration.
    """

    disk_params: DiskParams
    config: ModelConfig

    # Precomputed values (set in __post_init__)
    _sigma_g0: float = 0.0
    _sigma_s0: float = 0.0
    _snow_line: float = 0.0
    _inner_boundary: float = 0.0
    _gamma: float = 0.0
    _a_c: float = 0.0
    _stellar_mass: float = 0.0
    _perturbation_amp: float = 0.0
    _perturbation_f: float = 0.0

    def __post_init__(self) -> None:
        """Precompute normalization constants."""
        dp = self.disk_params
        cfg = self.config
        self._gamma = cfg.gamma
        self._a_c = dp.characteristic_radius
        self._stellar_mass = dp.stellar_mass
        self._perturbation_amp = cfg.perturbation_amplitude
        self._perturbation_f = cfg.perturbation_length_scale

        self._sigma_g0 = _compute_sigma_g0(dp.disk_mass, self._a_c, self._gamma)
        self._sigma_s0 = self._sigma_g0 * Z_0 * 10.0**dp.metallicity
        self._snow_line = _snow_line_au(dp.stellar_mass)
        self._inner_boundary = inner_boundary_au(dp.stellar_mass)

    def sigma_gas(self, r_au: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Gas surface density at given radii.

        Parameters
        ----------
        r_au : npt.NDArray[np.float64]
            Radial positions in AU.

        Returns
        -------
        npt.NDArray[np.float64]
            Gas surface density in g/cm^2.
        """
        x = r_au / self._a_c
        result: npt.NDArray[np.float64] = self._sigma_g0 * x ** (-self._gamma) * np.exp(-(x ** (2.0 - self._gamma)))
        return result

    def sigma_solids(self, r_au: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Solid surface density at given radii.

        Parameters
        ----------
        r_au : npt.NDArray[np.float64]
            Radial positions in AU.

        Returns
        -------
        npt.NDArray[np.float64]
            Solid surface density in g/cm^2.
        """
        x = r_au / self._a_c
        base: npt.NDArray[np.float64] = self._sigma_s0 * x ** (-self._gamma) * np.exp(-(x ** (2.0 - self._gamma)))
        eta_ice = np.where(r_au < self._snow_line, 0.25, 1.0)
        result: npt.NDArray[np.float64] = base * eta_ice

        if self._perturbation_amp > 0.0:
            h_r = _scale_height_au(r_au, self._stellar_mass)
            perturbation = 1.0 + self._perturbation_amp * np.cos(2.0 * np.pi * r_au / (self._perturbation_f * h_r))
            result = result * perturbation

        return result

    def initial_embryo_positions(self) -> list[float]:
        """Compute initial embryo positions from inner boundary outward.

        Uses isolation mass at each location to set the spacing,
        yielding ~10-60 embryos as in Miguel et al. (2011).

        Returns
        -------
        list[float]
            Semi-major axes of initial embryos in AU.
        """
        a_in = self._inner_boundary
        outer_edge = 5.0 * self._a_c

        positions: list[float] = [a_in]
        current = a_in
        while current < outer_edge:
            # Use local isolation mass for spacing
            r_arr = np.array([current])
            sig_s = float(self.sigma_solids(r_arr)[0])
            # Isolation mass ~ 2*pi*a*Delta_a*Sigma_s, self-consistent with spacing
            # Use a seed mass of 0.01 M_earth (lunar mass) as floor
            iso_mass = max(_isolation_mass_earth(current, sig_s, self._stellar_mass), 0.01)
            da = embryo_spacing_au(current, iso_mass, self._stellar_mass)
            da = max(da, 0.05 * current)  # floor: at least 5% of current radius
            current += da
            if current < outer_edge:
                positions.append(current)

        return positions


# ---------------------------------------------------------------------------
# Surface density normalization (computed once)
# ---------------------------------------------------------------------------


def _compute_sigma_g0(disk_mass: float, characteristic_radius: float, gamma: float) -> float:
    """Compute gas surface density normalization Sigma_g^0.

    Parameters
    ----------
    disk_mass : float
        Total disk mass in solar masses.
    characteristic_radius : float
        Characteristic radius a_c in AU.
    gamma : float
        Inner disk density exponent.

    Returns
    -------
    float
        Normalization Sigma_g^0 in g/cm^2.
    """
    a_c_cm = characteristic_radius * AU_CM
    disk_mass_g = disk_mass * M_SUN_G

    r_au = np.linspace(0.01, 10.0 * characteristic_radius, 10000)
    r_cm = r_au * AU_CM
    x = r_cm / a_c_cm
    profile = x ** (-gamma) * np.exp(-(x ** (2.0 - gamma)))
    integrand = profile * r_cm * 2.0 * np.pi
    integral = float(np.trapezoid(integrand, r_cm))

    if integral == 0.0:  # pragma: no cover
        return 0.0
    return disk_mass_g / integral


# ---------------------------------------------------------------------------
# Disk geometry helpers
# ---------------------------------------------------------------------------


def _snow_line_au(stellar_mass: float) -> float:
    """Approximate snow line location.

    Parameters
    ----------
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Snow line radius in AU.
    """
    luminosity = stellar_mass**4.0
    return float(2.7 * luminosity**0.5)


def _scale_height_au(r_au: npt.NDArray[np.float64], stellar_mass: float) -> npt.NDArray[np.float64]:
    """Disk scale height H(r).

    Parameters
    ----------
    r_au : npt.NDArray[np.float64]
        Radial positions in AU.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    npt.NDArray[np.float64]
        Scale height in AU.
    """
    luminosity = stellar_mass**4.0
    temp = 280.0 * (r_au ** (-0.5)) * luminosity**0.25
    mu = 2.34
    r_cm = r_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    cs_sq = K_BOLTZ * temp / (mu * M_PROTON)
    vk_sq = G_CGS * m_star_g / r_cm
    h_over_r = np.sqrt(cs_sq / vk_sq)
    result: npt.NDArray[np.float64] = r_au * h_over_r
    return result


# ---------------------------------------------------------------------------
# Inner boundary and embryo placement
# ---------------------------------------------------------------------------


def inner_boundary_au(stellar_mass: float) -> float:
    """Inner boundary of the dust disk (Eq. 6, Vinkovic 2006).

    Parameters
    ----------
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Inner boundary radius in AU.
    """
    luminosity = stellar_mass**4.0
    return float(0.0688 * (1500.0 / T_SUB) ** 2 * luminosity**0.5)


def _isolation_mass_earth(a_au: float, sigma_s: float, stellar_mass: float) -> float:
    """Local isolation mass estimate.

    Parameters
    ----------
    a_au : float
        Semi-major axis in AU.
    sigma_s : float
        Local solid surface density in g/cm^2.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Isolation mass in Earth masses.
    """
    r_cm = a_au * AU_CM
    m_star_g = stellar_mass * M_SUN_G
    # M_iso ~ (2*pi*a*b*Sigma_s)^{3/2} / (3*M*)^{1/2}
    # where b ~ 10 * r_Hill ~ 10 * a * (M_iso/(3*M*))^{1/3}
    # Solving self-consistently: M_iso ~ 0.16 * (Sigma_s * a^2)^{3/2} / M*^{1/2}
    # In CGS:
    sig_a2 = sigma_s * r_cm**2
    m_iso_g = 0.16 * sig_a2**1.5 / m_star_g**0.5
    return float(max(m_iso_g / M_EARTH_G, 1e-4))


def embryo_spacing_au(a_au: float, embryo_mass_earth: float, stellar_mass: float) -> float:
    """Spacing between embryos Delta_a (Eq. 7).

    Parameters
    ----------
    a_au : float
        Current semi-major axis in AU.
    embryo_mass_earth : float
        Initial embryo mass in Earth masses.
    stellar_mass : float
        Stellar mass in solar masses.

    Returns
    -------
    float
        Spacing in AU.
    """
    m_star_g = stellar_mass * M_SUN_G
    m_emb_g = embryo_mass_earth * 5.972e27
    return float(10.0 * (2.0 * m_emb_g / (3.0 * m_star_g)) ** (1.0 / 3.0) * a_au)


# ---------------------------------------------------------------------------
# Toomre stability check
# ---------------------------------------------------------------------------


def toomre_q(disk_params: DiskParams, config: ModelConfig) -> float:
    """Minimum Toomre Q parameter across the disk (Eq. 5).

    Parameters
    ----------
    disk_params : DiskParams
        Disk initial conditions.
    config : ModelConfig
        Model configuration.

    Returns
    -------
    float
        Minimum Q value. Q < 1 means gravitationally unstable.
    """
    gamma = config.gamma
    a_c = disk_params.characteristic_radius
    m_star = disk_params.stellar_mass
    sg0 = _compute_sigma_g0(disk_params.disk_mass, a_c, gamma)

    if sg0 == 0.0:  # pragma: no cover
        return float("inf")

    r_au = np.linspace(0.1, 5.0 * a_c, 1000)
    x = r_au / a_c
    sig_g = sg0 * x ** (-gamma) * np.exp(-(x ** (2.0 - gamma)))

    r_cm = r_au * AU_CM
    m_star_g = m_star * M_SUN_G
    omega = np.sqrt(G_CGS * m_star_g / r_cm**3)
    luminosity = m_star**4.0
    temp = 280.0 * (r_au ** (-0.5)) * luminosity**0.25
    mu = 2.34
    cs = np.sqrt(K_BOLTZ * temp / (mu * M_PROTON))

    q_values = cs * omega / (np.pi * G_CGS * sig_g)
    return float(np.min(q_values))


def is_stable(disk_params: DiskParams, config: ModelConfig) -> bool:
    """Check if a disk is gravitationally stable.

    Parameters
    ----------
    disk_params : DiskParams
        Disk initial conditions.
    config : ModelConfig
        Model configuration.

    Returns
    -------
    bool
        True if the disk is stable.
    """
    if disk_params.disk_mass > 0.2 * disk_params.stellar_mass:
        return False
    return toomre_q(disk_params, config) > 1.0
