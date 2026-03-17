---
sidebar_position: 3
---

# Run Log

All population synthesis runs executed on AWS Lambda.

## Runs

| Run ID             | Date       | N    | $\gamma$ | $c_\text{migI}$ | $A$  | Seed | Notes                               |
| ------------------ | ---------- | ---- | -------- | --------------- | ---- | ---- | ----------------------------------- |
| `run-8188747bb981` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.0  | 42   | Baseline smooth disk, no migration. |
| `run-b855d8de77ab` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.05 | 42   | Bifurcation sweep.                  |
| `run-fa19bcfe6c0c` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.1  | 42   | Bifurcation sweep.                  |
| `run-60436b7bb025` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.15 | 42   | Bifurcation sweep.                  |
| `run-55a2f3631bae` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.2  | 42   | Bifurcation sweep.                  |
| `run-fe328eff2004` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.25 | 42   | Bifurcation sweep.                  |
| `run-6612a232d668` | 2026-03-17 | 1000 | 1.0      | 0.0             | 0.3  | 42   | Transitional disk.                  |

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
