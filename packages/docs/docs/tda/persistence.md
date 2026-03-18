---
sidebar_position: 1
---

# Persistent Homology

## Method

We apply **Vietoris-Rips persistent homology** to the point cloud of consolidated planetary system architectures. Each of the $N = 4000$ simulated systems is represented as a point in $\mathbb{R}^6$:

$$
\mathbf{x}_i = (N_\text{giant},\;N_\text{terrestrial},\;M_\text{terr,tot},\;\bar{M}_\text{terr},\;\eta,\;R_\text{COM})
$$

Before computing persistence, all features are standardized (zero mean, unit variance) to ensure that no single dimension dominates the distance computation.

The computation uses [ripser](https://ripser.scikit-tda.org/) via the `topo-archeo` package:

```bash
uv run experiments persistence --run-id <run-id>
```

## Results: smooth disks ($A = 0$)

Run: [`run-f6f8c011173b`](../simulations/runs). Configuration: $\gamma = 1.0$, no migration, $A = 0$, $N = 4000$.

| Dimension | Persistent (lifetime > 0.5) | Max lifetime |
| --------- | --------------------------- | ------------ |
| $H_0$     | 91                          | 12.438       |
| $H_1$     | 4                           | 0.731        |

### $H_0$: Connected components (formation channels)

Top $H_0$ lifetimes:

```
12.438, 6.908, 5.709, 3.656, 2.902, 2.615, 2.370, 2.269
```

The dominant feature (lifetime 12.4) corresponds to the **giant/terrestrial binary split** -- the last two clusters to merge as the filtration scale increases. The large gap between the top lifetime (12.4) and the next (6.9) confirms that this is the most prominent topological feature of the architecture space.

### $H_1$: Loops (degeneracies in the inverse problem)

Four $H_1$ features survive above the 0.5 threshold, with lifetimes:

```
0.731, 0.665, 0.644, 0.549
```

These loops indicate regions of the architecture space where **topologically distinct families of disk initial conditions produce indistinguishable planetary architectures**. In the language of the inverse problem, these are irreducible degeneracies: there is no single-valued inverse for the forward map $F$ in these regions.

## Results: transitional disks ($A = 0.3$)

Run: [`run-1c2418226991`](../simulations/runs). Configuration: $\gamma = 1.0$, no migration, $A = 0.3$, $N = 4000$.

| Dimension | Persistent (lifetime > 0.5) | Max lifetime |
| --------- | --------------------------- | ------------ |
| $H_0$     | 97                          | 5.411        |
| $H_1$     | 0                           | 0.485        |

### $H_0$: Formation channels soften

Top $H_0$ lifetimes:

```
5.411, 4.505, 4.234, 3.093, 3.044, 2.678, 2.356, 2.165
```

The dominant cluster gap has dropped from 12.4 to 5.4, and the gap between the 1st and 2nd lifetimes is only 0.9. The density perturbation **softens the giant/terrestrial binary** into a more graded transition with multiple comparable cluster separations.

### $H_1$: All degeneracies resolved

No $H_1$ features survive above the 0.5 threshold. The maximum lifetime is only 0.485. The perturbation **completely resolves** the topological degeneracies present in the smooth disk case. At $A = 0.3$, the additional radial structure from dust traps provides enough information to make the inverse problem well-posed -- every architecture maps to a topologically connected region of disk initial conditions.

## Comparison: smooth vs transitional

| Feature                    | Smooth ($A = 0$) | Transitional ($A = 0.3$) |
| -------------------------- | ---------------- | ------------------------ |
| $H_0$ max lifetime         | 12.438           | 5.411                    |
| $H_0$ gap (1st - 2nd)      | 5.530            | 0.906                    |
| $H_1$ persistent ($> 0.5$) | **4**            | **0**                    |
| $H_1$ max lifetime         | 0.731            | 0.485                    |
| Giant planet fraction      | 31.6%            | 31.1%                    |

### Key finding: the topology changes

The transition from smooth to density-perturbed disks is **not merely a geometric deformation** of the outcome manifold. The Betti numbers change: $\beta_1 = 4 \to 0$ (at the 0.5 threshold). This answers the central question posed in Phase D of the project proposal:

> Does varying $A$ from 0 to 0.3 change the topology of the outcome space, or just its geometry?

**The topology changes.** Specifically:

1. The dominant $H_0$ cluster gap **closes** (12.4 $\to$ 5.4), indicating that the sharp giant/terrestrial binary softens into a more graded transition.

2. All four $H_1$ loops **die** when the perturbation is turned on, meaning all families of degenerate formation histories are **resolved** by the additional information from disk substructure.

3. The giant planet fraction remains essentially unchanged (31.6% vs 31.1%), confirming that the topological change is **not driven by a shift in classification fractions** but by a reorganization of the internal structure of the point cloud.

These results were inaccessible with the KDE-on-marginals approach used in the original paper. Persistent homology detects structure -- degeneracy loops and formation channel splits -- that marginal density estimates cannot represent.

## Next steps

1. **Fiber analysis** (Phase C): for systems near the $H_1$ loops in the smooth disk, examine the preimage $F^{-1}(y)$ to characterize the distinct formation histories that produce similar architectures.
2. **Migration sweep**: enable Type I migration ($c_\text{migI} = 0.01, 0.1, 1$) and track how the persistence diagrams change.
3. **Manifold learning** (Phase B): estimate the intrinsic dimension of $\text{im}(F)$ via UMAP or diffusion maps.
