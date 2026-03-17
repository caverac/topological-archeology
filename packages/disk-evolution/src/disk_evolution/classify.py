"""Planetary system classification following Miguel et al. (2011), Section 3.1.

Classifies simulated systems into six types based on planet masses
and semi-major axes.
"""

from __future__ import annotations

from enum import Enum

from disk_evolution.models import SystemArchitecture

MERCURY_MASS_EARTH: float = 0.055
"""Mercury mass in Earth masses, threshold for failed systems."""

GIANT_THRESHOLD: float = 15.0
"""Mass threshold for giant planets in Earth masses."""


class SystemType(Enum):
    """Planetary system classification types."""

    HOT_WARM_JUPITER = "hot_warm_jupiter"
    SOLAR = "solar"
    COMBINED = "combined"
    COLD_JUPITER = "cold_jupiter"
    LOW_MASS = "low_mass"
    FAILED = "failed"


def classify(architecture: SystemArchitecture) -> SystemType:
    """Classify a planetary system into one of six types.

    Classification follows Miguel et al. (2011), Section 3.1:

    - **Hot/warm Jupiters**: giants (M > 15 M_earth) at a < 1 AU, none between 1-30 AU.
    - **Solar systems**: giants between 1-30 AU, none inside 1 AU.
    - **Combined**: at least one giant within 1 AU AND at least one between 1-30 AU.
    - **Cold Jupiters**: giants only beyond 30 AU.
    - **Low mass**: all planets below 15 M_earth.
    - **Failed**: no planet exceeds Mercury mass (0.055 M_earth).

    Parameters
    ----------
    architecture : SystemArchitecture
        The simulated planetary system.

    Returns
    -------
    SystemType
        The classification.
    """
    planets = architecture.planets

    if not planets or all(p.total_mass < MERCURY_MASS_EARTH for p in planets):
        return SystemType.FAILED

    giants_inner = [p for p in planets if p.total_mass >= GIANT_THRESHOLD and p.semi_major_axis < 1.0]
    giants_mid = [p for p in planets if p.total_mass >= GIANT_THRESHOLD and 1.0 <= p.semi_major_axis <= 30.0]
    giants_outer = [p for p in planets if p.total_mass >= GIANT_THRESHOLD and p.semi_major_axis > 30.0]

    has_inner = len(giants_inner) > 0
    has_mid = len(giants_mid) > 0
    has_outer = len(giants_outer) > 0

    if has_inner and has_mid:
        return SystemType.COMBINED

    if has_inner and not has_mid:
        return SystemType.HOT_WARM_JUPITER

    if has_mid and not has_inner:
        return SystemType.SOLAR

    if has_outer and not has_inner and not has_mid:
        return SystemType.COLD_JUPITER

    return SystemType.LOW_MASS
