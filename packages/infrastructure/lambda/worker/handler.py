"""Worker Lambda: runs a single disk evolution simulation and writes results to S3."""

from __future__ import annotations

import json
import os
import uuid

import boto3

from disk_evolution.classify import classify
from disk_evolution.models import ConsolidatedOutput, DiskParams, ModelConfig
from disk_evolution.simulate import evolve_system, simulate_single

s3 = boto3.client("s3")

BUCKET = os.environ["BUCKET_NAME"]


def handler(event: dict[str, object], context: object) -> dict[str, object]:
    """Simulate one planetary system and upload results to S3.

    Expects a single SQS record whose body contains:
    - disk_params: {stellar_mass, disk_mass, characteristic_radius, metallicity, gas_dissipation_timescale}
    - config: {gamma, c_mig_i, perturbation_amplitude, ...}
    - run_id: string identifier for this batch
    - system_index: integer index within the batch

    Parameters
    ----------
    event : dict[str, object]
        Raw SQS event (batch_size=1).
    context : object
        Lambda runtime context.

    Returns
    -------
    dict[str, object]
        Response with statusCode 200 and the output S3 key.
    """
    records = event.get("Records", [])
    assert isinstance(records, list) and len(records) == 1
    record = records[0]
    assert isinstance(record, dict)
    body_str = record.get("body", "{}")
    assert isinstance(body_str, str)
    msg: dict[str, object] = json.loads(body_str)

    dp_raw = msg["disk_params"]
    assert isinstance(dp_raw, dict)
    disk_params = DiskParams(**dp_raw)

    cfg_raw = msg.get("config", {})
    assert isinstance(cfg_raw, dict)
    config = ModelConfig(**cfg_raw)

    run_id = str(msg.get("run_id", uuid.uuid4().hex))
    system_index = int(str(msg.get("system_index", 0)))

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
