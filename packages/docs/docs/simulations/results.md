---
sidebar_position: 2
---

# Partial Results

:::caution Work in Progress
These are preliminary results from the initial implementation. The model is being validated against Tables 2--4 of [Miguel et al. (2011)](https://arxiv.org/abs/1106.3281). Several physics parameters are still being tuned.
:::

## Validation target

Miguel et al. (2011) ran 1000 systems per configuration and reported the percentage of each system type. Our primary validation target is **Table 3** ($\gamma = 1.0$, no migration):

| Type                     | Miguel et al. (%) | Our result (N=50) |
| ------------------------ | ----------------- | ----------------- |
| Hot and warm Jupiters    | 1.8               | 0.0               |
| Solar systems            | 23.7              | **14.0**          |
| Cold Jupiters            | 0                 | 0.0               |
| Combined systems         | 0                 | 0.0               |
| Low mass planet systems  | 73.4              | **80.0**          |
| Failed planetary systems | 1.1               | 6.0               |

## What works

The simulation correctly reproduces the **qualitative structure** of the population:

1. **Low-mass systems dominate** (~80%), as expected from the core instability model -- most disks do not have enough solid material to form giant planet cores.

2. **Solar-type systems are the second most common** (~14%), formed in massive, metal-rich disks where isolation masses exceed 10 $M_\oplus$ at $r > 5$ AU.

3. **Giant planet formation proceeds via runaway gas accretion**, triggered when the solid accretion rate drops near isolation and $M_\text{crit}$ falls below $M_\text{core}$. In a test case at 8 AU with a massive disk ($M_d = 0.1\,M_\odot$, [Fe/H] = 0.2):
   - Core reaches 18 $M_\oplus$ by 0.5 Myr
   - Gas accretion triggers at ~0.7 Myr
   - Planet reaches Jupiter mass within a single timestep (runaway)

4. **No hot Jupiters form without migration**, consistent with the paper.

## Bugs found and fixed

Three significant bugs were identified and corrected during validation:

### 1. Isolation mass formula (factor ~1000x error)

The self-consistent isolation mass was computed with an incorrect coefficient:

```
# Wrong
m_iso = 0.16 * (sigma_s * r^2)^1.5 / m_star^0.5

# Correct
m_iso = (20 * pi * r^2 * sigma_s)^1.5 / (3 * m_star)^0.5
```

This gave isolation masses of ~0.001 $M_\oplus$ at the snow line instead of the correct ~2 $M_\oplus$.

### 2. Feeding zone width (factor 5x too narrow)

The feeding zone was defined as $2\,R_\text{Hill}$ instead of the embryo spacing $\Delta a = 10\,R_\text{Hill}$. This starved embryos at ~0.3 $M_\oplus$ instead of allowing them to reach their true isolation mass.

### 3. Accretion rate: Hill radius vs physical radius

The solid accretion formula (Eq. 9) uses the planet's **physical radius** $R_p$, not the Hill radius. Using the Hill radius inflated accretion rates by ~1000x, which in turn inflated $M_\text{crit}$ to >70 $M_\oplus$ and prevented gas accretion from ever triggering.

## Known discrepancies

### Fewer solar systems than expected

Our 14% vs the paper's 23.7%. Possible causes:

- **Small sample size**: 50 systems vs 1000. Statistical noise is significant.
- **Solid accretion rate details**: the gravitational focusing term and eccentricity equilibrium are simplified. The paper may use a more detailed prescription.
- **Collision growth**: embryos should merge more efficiently in the early phases, allowing cores to grow beyond their individual isolation masses. Our collision check runs once per timestep and may not capture rapid early merging.

### Higher failure rate

Our 6% vs the paper's 1.1%. This likely reflects embryos in low-mass disks that never grow beyond Mercury mass with our current accretion rate formula.

## Next steps

1. **Increase sample size** to 1000 systems for statistically meaningful comparison.
2. **Validate across all configurations**: Tables 2 ($\gamma = 0.5$) and 4 ($\gamma = 1.5$), and with migration enabled.
3. **Tune accretion physics**: compare solid accretion rates at specific (mass, radius, $\Sigma_s$) points against published values.
4. **Add transitional disk mode** ($A = 0.3$) and reproduce the Chaparro Molano comparison (Figures 1--4 of arXiv:1901.07078).
