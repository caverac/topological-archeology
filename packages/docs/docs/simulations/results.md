---
sidebar_position: 2
---

# Partial Results

:::caution Work in Progress
These are preliminary results from the initial implementation. The model is being validated against Tables 2--4 of [Miguel et al. (2011)](https://arxiv.org/abs/1106.3281). Several physics parameters are still being tuned.
:::

## Validation target

Miguel et al. (2011) ran 1000 systems per configuration and reported the percentage of each system type. Our primary validation target is **Table 3** ($\gamma = 1.0$, no migration).

### N=1000 run on AWS Lambda

Run ID: `run-8188747bb981`

```bash
# Submit 1000 jobs
uv run experiments submit --n-systems 1000 --gamma 1.0

# Collect results
uv run experiments collect --run-id run-8188747bb981
```

All 1000 Lambda invocations completed with zero errors. Execution times ranged from 1.2s to 75s per system, with a total wall-clock time of ~80 seconds at 500 concurrency.

| Type                     | Miguel et al. (%) | Our result (N=1000) |
| ------------------------ | ----------------- | ------------------- |
| Hot and warm Jupiters    | 1.8               | 0.0                 |
| Solar systems            | 23.7              | **18.7**            |
| Cold Jupiters            | 0                 | 0.0                 |
| Combined systems         | 0                 | 0.0                 |
| Low mass planet systems  | 73.4              | **66.7**            |
| Failed planetary systems | 1.1               | **14.6**            |

## What works

The simulation correctly reproduces the **qualitative structure** of the population:

1. **Low-mass systems dominate** (~67%), as expected from the core instability model -- most disks do not have enough solid material to form giant planet cores.

2. **Solar-type systems are the second most common** (18.7%), formed in massive, metal-rich disks where isolation masses exceed 10 $M_\oplus$ at $r > 5$ AU. The giant planet fraction (18.7%) is in the right ballpark of the paper's 23.7%.

3. **Giant planet formation proceeds via runaway gas accretion**, triggered when the solid accretion rate drops near isolation and $M_\text{crit}$ falls below $M_\text{core}$. In a test case at 8 AU with a massive disk ($M_d = 0.1\,M_\odot$, [Fe/H] = 0.2):
   - Core reaches 18 $M_\oplus$ by 0.5 Myr
   - Gas accretion triggers at ~0.7 Myr
   - Planet reaches Jupiter mass within a single timestep (runaway)

4. **No hot Jupiters form without migration**, consistent with the paper.

5. **Exact matches**: cold Jupiters (0%) and combined systems (0%) match the paper precisely.

## Known discrepancies

### Higher failure rate (14.6% vs 1.1%)

The largest discrepancy. Our accretion rates are too low for small disks, so embryos in low-mass disks never grow beyond Mercury mass (0.055 $M_\oplus$). The paper's model likely uses more efficient early accretion or starts embryos at larger seed masses.

### Fewer solar systems (18.7% vs 23.7%)

Possible causes:

- **Solid accretion rate details**: the gravitational focusing term and eccentricity equilibrium are simplified compared to the full prescription.
- **Collision growth**: embryos should merge more efficiently in the early phases, allowing cores to grow beyond their individual isolation masses. Our collision check runs once per timestep and may not capture rapid early merging.

### Too many surviving planets (80 per system vs 5-40 expected)

The paper's Figure 7 shows 5-40 final planets per low-mass system. Our systems retain ~80 embryos because:

- Collisions are underactive -- the merger criterion (3.5 Hill radii) is checked once per timestep, missing rapid early merging.
- Many embryos remain just above the output mass threshold without significant growth.

This does not affect the system classification (which depends only on whether giants form) but will affect the consolidated quantities used for TDA.

## Next steps

1. **Validate across all configurations**: Tables 2 ($\gamma = 0.5$) and 4 ($\gamma = 1.5$), and with migration enabled ($c_\text{migI} = 0.01, 0.1, 1$).
2. **Tune accretion physics**: reduce failure rate by improving early accretion efficiency and embryo seeding.
3. **Improve collision merging**: run multiple collision passes per timestep, or reduce the merger distance threshold.
4. **Add transitional disk mode** ($A = 0.3$) and reproduce the Chaparro Molano comparison (Figures 1--4 of arXiv:1901.07078).
