---
sidebar_position: 1
---

# Persistent Homology

## Method

We apply **Vietoris-Rips persistent homology** to the point cloud of consolidated planetary system architectures. Each of the $N = 1000$ simulated systems is represented as a point in $\mathbb{R}^6$:

$$
\mathbf{x}_i = (N_\text{giant},\;N_\text{terrestrial},\;M_\text{terr,tot},\;\bar{M}_\text{terr},\;\eta,\;R_\text{COM})
$$

Before computing persistence, all features are standardized (zero mean, unit variance) to ensure that no single dimension dominates the distance computation.

The computation uses [ripser](https://ripser.scikit-tda.org/) via the `topo-archeo` package:

```bash
uv run experiments persistence --run-id <run-id>
```

## Results: smooth disks ($A = 0$)

Run: [`run-8188747bb981`](../simulations/runs). Configuration: $\gamma = 1.0$, no migration, $A = 0$.

| Dimension | Total features | Finite features | Persistent (lifetime > 0.5) | Max lifetime |
| --------- | -------------- | --------------- | --------------------------- | ------------ |
| $H_0$     | 1000           | 999             | 92                          | 4.500        |
| $H_1$     | 372            | 372             | 3                           | 0.889        |

### $H_0$: Connected components (formation channels)

Top $H_0$ lifetimes:

```
4.500, 2.578, 2.227, 2.179, 1.826, 1.744, 1.637, 1.532, 1.530, 1.518
```

The dominant feature (lifetime 4.5) corresponds to the **giant/terrestrial binary split** -- the last two clusters to merge as the filtration scale increases. The large gap between the top lifetime (4.5) and the next (2.6) confirms that this is the most prominent topological feature of the architecture space.

The next tier of lifetimes (2.2-2.6) suggests **finer substructure within each class** -- possibly distinguishing high-mass vs low-mass terrestrial systems, or separating giant systems by the number of giant planets.

### $H_1$: Loops (degeneracies in the inverse problem)

Three $H_1$ features survive above the 0.5 threshold, with lifetimes:

```
0.889, 0.667, 0.518
```

These loops indicate regions of the architecture space where **topologically distinct families of disk initial conditions produce indistinguishable planetary architectures**. In the language of the inverse problem, these are irreducible degeneracies: there is no single-valued inverse for the forward map $F$ in these regions.

## Results: transitional disks ($A = 0.3$)

Run: [`run-6612a232d668`](../simulations/runs). Configuration: $\gamma = 1.0$, no migration, $A = 0.3$.

| Dimension | Total features | Finite features | Persistent (lifetime > 0.5) | Max lifetime |
| --------- | -------------- | --------------- | --------------------------- | ------------ |
| $H_0$     | 1001           | 1000            | 101                         | 3.638        |
| $H_1$     | 373            | 373             | 2                           | 0.576        |

### $H_0$: Formation channels shift

Top $H_0$ lifetimes:

```
3.638, 3.479, 2.759, 2.472, 2.284, 2.248, 2.222, 1.925, 1.912, 1.903
```

Unlike the smooth case, the transitional disk population has **two comparable top lifetimes** (3.64, 3.48) rather than a single dominant one (4.5). The density perturbation **splits the dominant formation channel** -- the giant/terrestrial binary is less sharp, suggesting that dust traps create intermediate pathways between the two regimes.

### $H_1$: Reduced degeneracy

Two $H_1$ features survive above the 0.5 threshold (vs three for smooth disks), with lifetimes:

```
0.576, 0.544
```

The perturbation **reduces topological degeneracy**. Fewer distinct formation histories map to the same architecture when dust traps are present. This makes physical sense: the additional radial structure from the density perturbation adds information to the formation process, partially breaking the degeneracy of the inverse problem.

## Comparison: smooth vs transitional

| Feature                    | Smooth ($A = 0$) | Transitional ($A = 0.3$) |
| -------------------------- | ---------------- | ------------------------ |
| $H_0$ max lifetime         | 4.500            | 3.638                    |
| $H_0$ gap (1st - 2nd)      | 1.922            | 0.159                    |
| $H_0$ persistent ($> 0.5$) | 92               | 101                      |
| $H_1$ persistent ($> 0.5$) | **3**            | **2**                    |
| $H_1$ max lifetime         | 0.889            | 0.576                    |
| Giant planet fraction      | 18.7%            | 21.1%                    |

### Key finding: the topology changes

The transition from smooth to density-perturbed disks is **not merely a geometric deformation** of the outcome manifold. The Betti numbers change: $\beta_1 = 3 \to 2$ (at the 0.5 threshold). This answers the central question posed in Phase D of the project proposal:

> Does varying $A$ from 0 to 0.3 change the topology of the outcome space, or just its geometry?

**The topology changes.** Specifically:

1. The dominant $H_0$ cluster gap **closes** (4.5 $\to$ 3.6), and a second comparable gap **emerges** (3.5), indicating that the sharp giant/terrestrial binary softens into a more graded transition.

2. One $H_1$ loop **dies** when the perturbation is turned on, meaning one family of degenerate formation histories is **resolved** by the additional information from disk substructure.

3. The density perturbation creates **more giant planet systems** (21.1% vs 18.7%), consistent with the finding by Chaparro Molano et al. (2019) that transitional disks favor giant planet formation through over-dense regions.

These results were inaccessible with the KDE-on-marginals approach used in the original paper. Persistent homology detects structure -- degeneracy loops and formation channel splits -- that marginal density estimates cannot represent.

## Next steps

1. **Fiber analysis** (Phase C): for systems near the $H_1$ loops, examine the preimage $F^{-1}(y)$ to characterize the distinct formation histories that produce similar architectures.
2. **Bifurcation sweep** (Phase D): run at intermediate values of $A$ (0.05, 0.1, 0.15, 0.2, 0.25) to identify the critical threshold where the $H_1$ feature dies.
3. **Migration sweep**: enable Type I migration ($c_\text{migI} = 0.01, 0.1, 1$) and track how the persistence diagrams change.
4. **Manifold learning** (Phase B): estimate the intrinsic dimension of $\text{im}(F)$ via UMAP or diffusion maps.
