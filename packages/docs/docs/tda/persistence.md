---
sidebar_position: 1
---

# Persistent Homology

## Method

The archeology question asks: given an observed planetary system, what can we infer about its natal disk? Formally, the planet formation model defines a forward map $F: \mathcal{D} \to \mathcal{A}$ from the space of disk initial conditions to the space of planetary architectures. The inverse problem is to characterize $F^{-1}(\mathbf{y})$ -- the set of all disk configurations that could have produced a given architecture $\mathbf{y}$.

Two pathological scenarios can arise:

1. **Degeneracy**: $F^{-1}(\mathbf{y})$ is **disconnected** -- topologically distinct regions of disk space produce indistinguishable architectures. No amount of observational precision can resolve the ambiguity; the inverse problem is fundamentally ill-posed in that region.

2. **Bifurcation**: small changes in disk parameters cause **qualitative jumps** in the architecture -- the forward map has fold singularities that separate formation channels.

KDE-on-marginals, as used by [Chaparro Molano et al. (2019)](https://arxiv.org/abs/1901.07078), estimates the density of architectures but cannot detect either of these structures. Density tells you _where_ architectures cluster, not _how_ the clusters connect or whether loops exist.

**Persistent homology** (see [Preliminaries](preliminaries) for the mathematical background) detects exactly these structures:

- **$H_0$ (connected components)** tracks how the point cloud fragments into clusters as we vary a scale parameter. Long-lived $H_0$ features correspond to well-separated **formation channels** -- groups of architectures that remain distinct over a wide range of scales. The lifetime measures the separation between channels in the standardized feature space.

- **$H_1$ (loops)** detects 1-dimensional holes in the point cloud. In the context of disk archeology, a persistent $H_1$ loop means there exist architectures $\mathbf{y}$ such that the preimage $F^{-1}(\mathbf{y})$ wraps around in a topologically nontrivial way -- different formation pathways that produce similar outcomes form a closed circuit in architecture space. These are the **irreducible degeneracies** of the inverse problem.

### Point cloud construction

Each of the $N = 4000$ simulated systems is represented as a point in $\mathbb{R}^6$:

$$
\mathbf{x}_i = (N_\text{giant},\;N_\text{terrestrial},\;M_\text{terr,tot},\;\bar{M}_\text{terr},\;\eta,\;R_\text{COM})
$$

These six consolidated quantities summarize the architecture of each system. The choice of summary statistics follows [Chaparro Molano et al. (2019)](https://arxiv.org/abs/1901.07078), ensuring comparability with their KDE analysis.

### Preprocessing

Three of the six features -- total terrestrial mass, average terrestrial mass, and mass efficiency -- span multiple orders of magnitude and have heavily right-skewed distributions (skewness 2--8). Applying standard scaling directly to these features creates artificial outliers in the tail that dominate the persistence computation, producing spurious long-lived $H_0$ features that reflect extreme individual systems rather than cluster structure.

We apply **log1p transform** ($x \mapsto \log(1 + x)$) to these three features before standardization. This is motivated by the observation that these quantities are approximately **log-normally distributed** -- a consequence of the multiplicative processes (accretion, gas capture) that determine planetary masses.

After log-transformation, all six features are **standardized** (zero mean, unit variance) so that no single dimension dominates the Euclidean distance computation.

:::note Preprocessing matters
Without the log-transform, linear standardization produces 4 apparent $H_1$ loops for smooth disks that vanish with just 2% outlier removal -- they are artifacts of the heavy tails, not genuine topological structure. With the log-transform, 1 $H_1$ loop survives regardless of outlier treatment, confirming it is a robust feature.
:::

### Computation

We compute Vietoris--Rips persistent homology up to dimension 1 using [ripser](https://ripser.scikit-tda.org/) via the `topo-archeo` package. The Vietoris--Rips complex grows balls of radius $\epsilon$ around each point and connects points whose balls overlap. As $\epsilon$ increases from 0 to $\infty$, topological features (components, loops) are born and die. Each feature is characterized by its **persistence** (lifetime = death $-$ birth). Features with high persistence reflect genuine structure; features with low persistence are noise.

We use a **threshold of 0.5 standard deviations** to separate significant features from noise, and report both the count of persistent features and the maximum lifetime in each homology dimension.

```bash
uv run experiments persistence --run-id <run-id>
```

## Results: smooth disks ($A = 0$)

Run: [`run-f6f8c011173b`](../simulations/runs). Configuration: $\gamma = 1.0$, no migration, $A = 0$, $N = 4000$.

| Dimension | Persistent (lifetime > 0.5) | Max lifetime |
| --------- | --------------------------- | ------------ |
| $H_0$     | --                          | 12.067       |
| $H_1$     | 1                           | 0.743        |

### $H_0$: Formation channels

Top $H_0$ lifetimes:

```
12.067, 2.473, 2.299, 2.057, 2.001, 2.001, 1.808, 1.607
```

The dominant $H_0$ feature (lifetime 12.1) is driven by a small number of systems with extreme values of $N_\text{giant}$ (up to 7 giant planets), which remain outliers even after log-transformation of the mass features. The next tier of lifetimes ($\sim$2.0--2.5) reflects the separation between systems with and without giant planets, and between high- and low-mass terrestrial populations.

The $H_0$ structure indicates that the architecture space has **multiple distinct formation channels** with varying degrees of separation, but the dominant feature is sensitive to rare extreme systems rather than reflecting the primary giant/terrestrial divide.

### $H_1$: Degeneracy in the inverse problem

One $H_1$ feature survives above the 0.5 threshold, with lifetime **0.743**.

This loop represents a region of the architecture space where **topologically distinct families of disk initial conditions produce indistinguishable planetary architectures**. Concretely: there exist architectures near this loop where the preimage $F^{-1}(\mathbf{y})$ has multiple disconnected components. Different formation histories -- different combinations of disk mass, metallicity, and gas dissipation timescale -- lead to the same consolidated architecture vector.

This degeneracy is **robust** to preprocessing choices: it persists with and without outlier clipping, and across different log-transform configurations.

## Results: transitional disks ($A = 0.3$)

Run: [`run-1c2418226991`](../simulations/runs). Configuration: $\gamma = 1.0$, no migration, $A = 0.3$, $N = 4000$.

| Dimension | Persistent (lifetime > 0.5) | Max lifetime |
| --------- | --------------------------- | ------------ |
| $H_0$     | --                          | 4.782        |
| $H_1$     | 0                           | 0.437        |

### $H_0$: Formation channels soften

Top $H_0$ lifetimes:

```
4.782, 3.589, 3.063, 2.152, 2.089, 2.089, 1.584, 1.580
```

The dominant $H_0$ lifetime drops from 12.1 to 4.8. Even accounting for the outlier sensitivity, this represents a genuine **softening of the cluster structure**: the density perturbation creates intermediate formation pathways that reduce the separation between the most distinct populations.

Physically, the cosine density perturbation creates alternating over-dense and under-dense radial zones that provide additional sites for planet formation, blurring the sharp boundaries between formation channels.

### $H_1$: Degeneracy resolved

No $H_1$ features survive above the 0.5 threshold. The maximum lifetime is only 0.437. The perturbation **resolves the degeneracy** present in the smooth disk case.

At $A = 0.3$, the additional radial structure from dust traps provides enough information to make the inverse problem **topologically well-posed** -- every architecture maps to a connected region of disk initial conditions. The loop that existed in the smooth disk (lifetime 0.74) has been killed by the perturbation.

## Comparison: smooth vs transitional

| Feature                    | Smooth ($A = 0$) | Transitional ($A = 0.3$) |
| -------------------------- | ---------------- | ------------------------ |
| $H_0$ max lifetime         | 12.067           | 4.782                    |
| $H_0$ gap (1st - 2nd)      | 9.595            | 1.192                    |
| $H_1$ persistent ($> 0.5$) | **1**            | **0**                    |
| $H_1$ max lifetime         | 0.743            | 0.437                    |
| Giant planet fraction      | 31.6%            | 31.1%                    |

![Persistence diagrams](/img/results/persistence-diagrams.png)

_Persistence diagrams for smooth ($A = 0$, top row) and transitional ($A = 0.3$, bottom row) disks. Left: $H_0$ (connected components); right: $H_1$ (loops). Each dot represents a topological feature; its distance from the diagonal measures its persistence (lifetime). The smooth disk shows one persistent $H_1$ feature ($\beta_1 = 1$), while the transitional disk shows none ($\beta_1 = 0$)._

### Key finding: the topology changes

The transition from smooth to density-perturbed disks changes the topology of the outcome space:

1. **The $H_1$ degeneracy is resolved**: the smooth disk has one persistent loop (lifetime 0.74) that dies when the perturbation is turned on. This means one family of degenerate formation histories is resolved by the additional information from disk substructure.

2. **The $H_0$ cluster structure softens**: the dominant cluster separation drops from 12.1 to 4.8, and the gap between the 1st and 2nd lifetimes drops from 9.6 to 1.2. The perturbation smooths the boundaries between formation channels.

3. **The population fractions are invariant**: the giant planet fraction remains at ~31% across both configurations. The topological change is **not driven by a shift in classification fractions** but by a reorganization of the internal structure of the point cloud. This is the kind of structure that KDE-on-marginals cannot detect: the marginal distributions are nearly identical, but the topology differs.

## Next steps

1. **Fiber analysis** (Phase C): for systems near the $H_1$ loop in the smooth disk, examine the preimage $F^{-1}(y)$ to identify the distinct formation histories that produce similar architectures.
2. **Migration sweep**: enable Type I migration ($c_\text{migI} = 0.01, 0.1, 1$) and track how the persistence diagrams change.
3. **Manifold learning** (Phase B): estimate the intrinsic dimension of $\text{im}(F)$ via UMAP or diffusion maps.
