"""Worker Lambda: runs a single disk evolution simulation and writes results to S3."""

from __future__ import annotations

import json
import os
import uuid
from typing import TypedDict

import boto3

from disk_evolution.classify import classify
from disk_evolution.models import ConsolidatedOutput, DiskParams, ModelConfig
from disk_evolution.simulate import evolve_system, simulate_single


class _SQSRecord(TypedDict):
    """Minimal SQS record shape."""

    body: str


class SQSEvent(TypedDict):
    """Minimal SQS event shape (batch_size=1)."""

    Records: list[_SQSRecord]


class _SimulationMessage(TypedDict, total=False):
    """JSON body of the SQS message."""

    disk_params: dict[str, float]
    config: dict[str, float]
    run_id: str
    system_index: int


class LambdaResponse(TypedDict):
    """Lambda return shape."""

    statusCode: int
    body: dict[str, str]


s3 = boto3.client("s3")

BUCKET = os.environ["BUCKET_NAME"]


def handler(event: SQSEvent, context: object) -> LambdaResponse:
    """Simulate one planetary system and upload results to S3.

    Expects a single SQS record whose body contains:
    - disk_params: {stellar_mass, disk_mass, characteristic_radius, metallicity, gas_dissipation_timescale}
    - config: {gamma, c_mig_i, perturbation_amplitude, ...}
    - run_id: string identifier for this batch
    - system_index: integer index within the batch

    Parameters
    ----------
    event : SQSEvent
        Raw SQS event (batch_size=1).
    context : object
        Lambda runtime context (unused).

    Returns
    -------
    LambdaResponse
        Response with statusCode 200 and the output S3 key.
    """
    records = event["Records"]
    assert len(records) == 1
    msg: _SimulationMessage = json.loads(records[0]["body"])

    disk_params = DiskParams(**msg["disk_params"])

    cfg_raw = msg.get("config", {})
    config = ModelConfig(**cfg_raw)

    run_id = msg.get("run_id", uuid.uuid4().hex)
    system_index = msg.get("system_index", 0)

    architecture = evolve_system(disk_params, config)
    consolidated = simulate_single(disk_params, config)
    system_type = classify(architecture)

    result = {
        "system_index": system_index,
        "disk_params": {
            "stellar_mass": disk_params.stellar_mass,
            "disk_mass": disk_params.disk_mass,
            "characteristic_radius": disk_params.characteristic_radius,
            "metallicity": disk_params.metallicity,
            "gas_dissipation_timescale": disk_params.gas_dissipation_timescale,
        },
        "config": {
            "gamma": config.gamma,
            "c_mig_i": config.c_mig_i,
            "perturbation_amplitude": config.perturbation_amplitude,
        },
        "planets": [
            {
                "semi_major_axis": p.semi_major_axis,
                "total_mass": p.total_mass,
                "core_mass": p.core_mass,
            }
            for p in architecture.planets
        ],
        "consolidated": {
            "n_giant": consolidated.n_giant,
            "n_terrestrial": consolidated.n_terrestrial,
            "total_terrestrial_mass": consolidated.total_terrestrial_mass,
            "avg_terrestrial_mass": consolidated.avg_terrestrial_mass,
            "mass_efficiency": consolidated.mass_efficiency,
            "center_of_mass": consolidated.center_of_mass,
        },
        "system_type": system_type.value,
    }

    output_key = f"results/{run_id}/{system_index:06d}.json"
    s3.put_object(
        Bucket=BUCKET,
        Key=output_key,
        Body=json.dumps(result),
        ContentType="application/json",
    )

    return {"statusCode": 200, "body": {"output_key": output_key}}
