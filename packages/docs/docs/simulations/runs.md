---
sidebar_position: 3
---

# Run Log

All population synthesis runs executed on AWS Lambda.

## Runs

| Run ID | Date | N   | $\gamma$ | $c_\text{migI}$ | $A$ | Seed | Notes                                                                                 |
| ------ | ---- | --- | -------- | --------------- | --- | ---- | ------------------------------------------------------------------------------------- |
|        |      |     |          |                 |     |      | _Pending re-run after physics fixes (isolation mass seeding, multi-pass collisions)._ |

## How to inspect a run

```bash
# View classification summary and run metadata
uv run experiments collect --run-id <run-id>

# Run persistent homology on the results
uv run experiments persistence --run-id <run-id>
```

## How to add a run

1. Submit jobs:

```bash
uv run experiments submit --n-systems 1000 --gamma 1.0 --c-mig-i 0.1 --perturbation 0.3
```

2. Note the `run-id` printed by the command.
3. After completion, verify with `collect` and add a row to the table above.
