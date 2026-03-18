---
sidebar_position: 3
---

# Run Log

All population synthesis runs executed on AWS Lambda.

## Runs

| Run ID             | Date       | N    | $\gamma$ | $c_\text{migI}$ | $A$  | Seed | Notes                        |
| ------------------ | ---------- | ---- | -------- | --------------- | ---- | ---- | ---------------------------- |
| `run-4fbfbf5831c8` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.0  | 42   | Calibration run (pre-sweep). |
| `run-f6f8c011173b` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.0  | 42   | Bifurcation sweep.           |
| `run-4d4fd342fa0b` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.05 | 42   | Bifurcation sweep.           |
| `run-29eccac6b444` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.1  | 42   | Bifurcation sweep.           |
| `run-1e25f9cc438f` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.15 | 42   | Bifurcation sweep.           |
| `run-efb98c3d0ffc` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.2  | 42   | Bifurcation sweep.           |
| `run-83a1157e25d9` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.25 | 42   | Bifurcation sweep.           |
| `run-1c2418226991` | 2026-03-18 | 4000 | 1.0      | 0.0             | 0.3  | 42   | Bifurcation sweep.           |

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
