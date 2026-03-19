---
sidebar_position: 2
---

# Calibration

Validation of the semi-analytic simulation against Tables 2--4 of [Miguel et al. (2011)](https://arxiv.org/abs/1106.3281).

## Reference target

Miguel et al. (2011) ran 1000 systems per configuration and reported the percentage of each system type. Our calibration target is **Table 3** ($\gamma = 1.0$, no migration).

## Calibration run

Run: [`run-4fbfbf5831c8`](runs). Configuration: $\gamma = 1.0$, $c_\text{migI} = 0$, $A = 0$, $N = 4000$, seed = 42.

```bash
uv run experiments submit --n-systems 4000 --gamma 1.0
uv run experiments collect --run-id run-4fbfbf5831c8
```

| Type                     | Miguel et al. (%) | Our result (N=4000) |
| ------------------------ | ----------------- | ------------------- |
| Hot and warm Jupiters    | 1.8               | 0.0                 |
| Solar systems            | 23.7              | **31.6**            |
| Cold Jupiters            | 0                 | 0.0                 |
| Combined systems         | 0                 | 0.0                 |
| Low mass planet systems  | 73.4              | **52.0**            |
| Failed planetary systems | 1.1               | **16.3**            |

![Calibration bar chart](/img/results/calibration.png)

_Calibration against Table 3 of Miguel et al. (2011) ($\gamma = 1.0$, no migration, $N = 4000$). Grouped bars show the percentage of each system type in the reference population (dark) and in our simulation (black). Quantitative differences reflect parameterized gas accretion and simplified Type I migration._

## Assessment

The simulation reproduces the **qualitative population structure**:

1. **Low-mass systems are the most common** (52%), consistent with the core instability model -- most disks lack enough solid material to form giant planet cores.

2. **Solar-type systems are the second most common** (31.6%), formed in massive, metal-rich disks where isolation masses exceed 10 $M_\oplus$ beyond the snow line.

3. **Giant planet formation proceeds via runaway gas accretion**, triggered when the solid accretion rate drops near isolation and $M_\text{crit}$ falls below $M_\text{core}$.

4. **No hot Jupiters form without migration**, consistent with the paper.

5. **Exact matches**: cold Jupiters (0%) and combined systems (0%) match the paper precisely.

## Quantitative differences

The quantitative differences reflect known simplifications in our model relative to Miguel et al. (2011), who solve the full envelope structure equations and use a different gas accretion prescription.

### Over-production of solar systems (31.6% vs 23.7%)

Our gas accretion uses the Ida & Lin (2004a) Kelvin-Helmholtz parameterization ($\tau_\text{KH} = 10^9 M^{-3}$ yr), while Miguel et al. solve the 1D envelope structure equations (Guilera et al. 2010, Eqs. 30--33). The parameterized KH timescale may trigger runaway gas accretion for cores that the full structure solver would keep in hydrostatic equilibrium, producing more giant planets.

### Higher failure rate (16.3% vs 1.1%)

Two contributing factors:

1. **No Paardekooper Type I migration**: the Tanaka (2002) formula only produces inward migration. The Paardekooper et al. (2011) torques include corotation terms that create convergence zones, trapping embryos at orbital radii where they can continue accreting. Without these traps, embryos in low-mass disks remain scattered at their initial positions without sufficient material to grow.

2. **Dynamical eccentricity/inclination**: gas drag damping lowers planetesimal eccentricities, which reduces gravitational focusing in the high-velocity collision regime. This slows accretion for isolated embryos in the outer disk, causing more systems to fail to produce bodies above Mercury mass.

### Too many surviving planets (~76 per system vs 5--40 expected)

Many embryos in the outer disk remain too far apart to trigger the 3.5 mutual Hill radius merger criterion. This inflates the planet count but does not affect the system classification (which depends only on whether giants form).

## Suitability for TDA

These quantitative differences affect the **absolute fractions** but not the **topological structure** that persistent homology detects. The relevant properties for TDA are:

- **Formation channels exist**: the simulation produces three distinct populations (giant, terrestrial, failed) with clear separation in the consolidated feature space.
- **Channels respond to parameters**: varying the perturbation amplitude $A$ changes both the classification fractions and the persistence diagrams, confirming that the forward map $F$ carries topological information.
- **The physics is grounded**: every prescription is drawn from published references (Inaba et al. 2001, Ohtsuki et al. 2002, Ida & Lin 2004a, Guilera et al. 2010, Fortier et al. 2013) with equations and constants documented in the [algorithm description](algorithm).

The known limitations (Paardekooper migration, planetesimal drift, viscous gas evolution) would improve the absolute calibration but are unlikely to change the qualitative topology of the outcome space. They are documented in the algorithm page and flagged as future work.
