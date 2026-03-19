"""Pydantic models for simulation result JSON schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ConsolidatedResult(BaseModel):
    """Consolidated summary quantities for a single planetary system."""

    n_giant: int
    n_terrestrial: int
    total_terrestrial_mass: float
    avg_terrestrial_mass: float
    mass_efficiency: float
    center_of_mass: float


class PlanetResult(BaseModel):
    """Per-planet output from a simulation."""

    semi_major_axis: float
    total_mass: float
    core_mass: float


class DiskParamsResult(BaseModel):
    """Disk initial conditions as stored in result JSON."""

    stellar_mass: float
    disk_mass: float
    characteristic_radius: float
    metallicity: float
    gas_dissipation_timescale: float


class SimulationConfig(BaseModel):
    """Fixed model parameters as stored in result JSON."""

    gamma: float = 1.0
    c_mig_i: float = 0.0
    perturbation_amplitude: float = 0.0


class SimulationResult(BaseModel):
    """A single simulation result as written by the Lambda handler."""

    system_index: int = 0
    disk_params: DiskParamsResult
    config: SimulationConfig
    planets: list[PlanetResult]
    consolidated: ConsolidatedResult
    system_type: str


class RunManifest(BaseModel):
    """Manifest metadata for a population synthesis run."""

    run_id: str = ""
    created_at: str = ""
    n_systems: int = 0
    seed: int = 0
    config: SimulationConfig = SimulationConfig()
