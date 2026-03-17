"""Submit simulation jobs to SQS for Lambda processing."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import boto3
import click
from disk_evolution.models import ModelConfig
from disk_evolution.priors import draw_population
from rich.console import Console

QUEUE_NAME = "topo-archeo-simulations"
BUCKET_PREFIX = "topo-archeo"


@click.command()
@click.option("--gamma", type=float, default=1.0, help="Disk density profile exponent.")
@click.option("--c-mig-i", type=float, default=0.0, help="Type I migration delay factor.")
@click.option("--perturbation", type=float, default=0.0, help="Perturbation amplitude A.")
@click.option("--n-systems", type=int, default=1000, help="Number of systems to simulate.")
@click.option("--seed", type=int, default=42, help="Random seed.")
@click.option("--run-id", type=str, default="", help="Run ID (auto-generated if empty).")
@click.option("--queue-url", type=str, default="", help="SQS queue URL (auto-discovered if empty).")
@click.option("--environment", type=str, default="development", help="Deployment environment.")
def submit(
    gamma: float,
    c_mig_i: float,
    perturbation: float,
    n_systems: int,
    seed: int,
    run_id: str,
    queue_url: str,
    environment: str,
) -> None:
    """Submit N simulation jobs to SQS for parallel Lambda execution."""
    console = Console()

    if not run_id:
        run_id = f"run-{uuid.uuid4().hex[:12]}"

    config = ModelConfig(gamma=gamma, c_mig_i=c_mig_i, perturbation_amplitude=perturbation)

    console.print(f"[bold]Drawing {n_systems} disk initial conditions (seed={seed})...[/bold]")
    disk_params_list = draw_population(n_systems, config, seed=seed)

    if not queue_url:
        sqs = boto3.client("sqs")
        resp = sqs.get_queue_url(QueueName=QUEUE_NAME)
        queue_url = resp["QueueUrl"]

    sqs = boto3.client("sqs")

    config_dict = {
        "gamma": config.gamma,
        "c_mig_i": config.c_mig_i,
        "perturbation_amplitude": config.perturbation_amplitude,
        "perturbation_length_scale": config.perturbation_length_scale,
        "total_time": config.total_time,
        "dt": config.dt,
    }

    # Write manifest to S3
    bucket = f"{BUCKET_PREFIX}-{environment}-data"
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_systems": n_systems,
        "seed": seed,
        "config": config_dict,
    }
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=f"results/{run_id}/manifest.json",
        Body=json.dumps(manifest, indent=2),
        ContentType="application/json",
    )

    console.print(f"[bold]Submitting {n_systems} jobs to {QUEUE_NAME}...[/bold]")
    console.print(f"  run_id: [cyan]{run_id}[/cyan]")
    console.print(f"  config: gamma={gamma}, c_mig_i={c_mig_i}, A={perturbation}")

    for i, dp in enumerate(disk_params_list):
        msg = {
            "run_id": run_id,
            "system_index": i,
            "disk_params": {
                "stellar_mass": dp.stellar_mass,
                "disk_mass": dp.disk_mass,
                "characteristic_radius": dp.characteristic_radius,
                "metallicity": dp.metallicity,
                "gas_dissipation_timescale": dp.gas_dissipation_timescale,
            },
            "config": config_dict,
        }
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(msg))

        if (i + 1) % max(1, n_systems // 10) == 0:
            console.print(f"  [{i + 1}/{n_systems}] sent")

    console.print(f"[bold green]Done. {n_systems} jobs submitted.[/bold green]")
    console.print(f"Collect results with: experiments collect --run-id {run_id}")
