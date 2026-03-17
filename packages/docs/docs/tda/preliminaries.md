---
sidebar_position: 0
---

# Preliminaries

## What is Topological Data Analysis?

Topological Data Analysis (TDA) is a family of methods that extract **qualitative, coordinate-free features** from data by studying its shape. Where classical statistics summarizes data through moments, densities, and projections, TDA characterizes the **connected components, loops, cavities, and higher-dimensional voids** that persist across multiple scales of resolution.

The central premise is that data sampled from an underlying space inherits topological structure from that space, and that this structure carries information that is invisible to traditional statistical summaries. TDA makes this precise through the language of algebraic topology -- specifically, **homology groups** -- applied to combinatorial approximations of the data (Carlsson, 2009).

### A brief history

TDA emerged in the early 2000s from the convergence of three threads:

1. **Computational topology.** Edelsbrunner, Letscher, and Zomorodian (2002) introduced the **persistence algorithm**, which tracks topological features across a filtration of simplicial complexes. This gave topology a computable, multi-scale character suited to noisy data.

2. **Topological inference.** Niyogi, Smale, and Weinberger (2008) proved that the homology of a manifold can be recovered from a sufficiently dense finite sample, grounding the intuition that "point cloud topology approximates manifold topology" in rigorous probability bounds.

3. **Applied algebraic topology.** Carlsson (2009) articulated the program of TDA as a discipline: use functorial constructions (filtrations, persistence modules) to assign robust topological invariants to datasets, and interpret those invariants in domain terms.

Since then, TDA has been applied in neuroscience (Giusti et al., 2015), materials science (Hiraoka et al., 2016), cosmology (Xu et al., 2019), genomics (Rabadan & Blumberg, 2019), and machine learning (Hensel et al., 2021).

## Simplicial complexes and homology

### From point clouds to simplicial complexes

Given a finite set of points $X = \{x_1, \ldots, x_N\} \subset \mathbb{R}^d$, we need a combinatorial object that captures the "shape" of $X$. A **simplicial complex** $K$ on $X$ is a collection of subsets (simplices) of $X$ that is closed under taking subsets:

- **0-simplices** (vertices): individual points $\{x_i\}$
- **1-simplices** (edges): pairs $\{x_i, x_j\}$
- **2-simplices** (triangles): triples $\{x_i, x_j, x_k\}$
- **$k$-simplices**: $(k+1)$-element subsets

The two most common constructions from a point cloud are:

**Vietoris-Rips complex.** For a scale parameter $\epsilon > 0$, the Rips complex $\mathrm{VR}_\epsilon(X)$ includes a $k$-simplex $\{x_{i_0}, \ldots, x_{i_k}\}$ whenever all pairwise distances satisfy $d(x_{i_a}, x_{i_b}) \leq \epsilon$. This is determined entirely by pairwise distances, making it easy to compute but potentially large.

**Alpha complex.** Built from the Delaunay triangulation restricted to balls of radius $\epsilon/2$. It has the same homology as the Cech complex (the "nerve" of $\epsilon$-balls) but with far fewer simplices in low ambient dimension. For data in $\mathbb{R}^d$ with $d \leq 3$, alpha complexes are the most efficient choice (Edelsbrunner & Harer, 2010).

### Homology groups

The **$k$-th homology group** $H_k(K)$ of a simplicial complex $K$ encodes the $k$-dimensional "holes" in $K$:

- $H_0(K)$: **connected components.** $\beta_0 = \mathrm{rank}(H_0) = $ number of connected components.
- $H_1(K)$: **loops** that are not boundaries of 2-simplices. $\beta_1 = $ number of independent non-trivial loops.
- $H_2(K)$: **voids** (enclosed cavities). $\beta_2 = $ number of independent enclosed voids.

The ranks $\beta_k = \mathrm{rank}(H_k)$ are called **Betti numbers**. They are topological invariants: they do not depend on the coordinates, metric, or embedding of the complex, only on its connectivity structure. This invariance is what makes them robust to noise and coordinate changes.

Homology is computed via **boundary operators** $\partial_k: C_k \to C_{k-1}$ that map $k$-chains (formal sums of $k$-simplices) to their $(k-1)$-dimensional boundaries. The $k$-th homology group is the quotient:

$$
H_k(K) = \ker(\partial_k) \,/\, \mathrm{im}(\partial_{k+1})
$$

Elements of $\ker(\partial_k)$ are **cycles** (chains with no boundary); elements of $\mathrm{im}(\partial_{k+1})$ are **boundaries** (cycles that bound a higher-dimensional chain). Homology classes are cycles modulo boundaries -- loops that are not "filled in."

## Persistent homology

### The problem of scale

A single simplicial complex at a fixed scale $\epsilon$ captures the topology of $X$ only if $\epsilon$ happens to match the "true" scale of the underlying structure. Too small, and the complex is disconnected dust; too large, and everything merges into a single blob. Real data has structure at **multiple scales simultaneously**, and the right $\epsilon$ is unknown.

**Persistent homology** solves this by studying the topology across **all scales at once** (Edelsbrunner et al., 2002; Zomorodian & Carlsson, 2005).

### Filtrations

A **filtration** is a nested sequence of simplicial complexes indexed by a scale parameter:

$$
\emptyset = K_0 \subseteq K_1 \subseteq K_2 \subseteq \cdots \subseteq K_m = K
$$

For the Vietoris-Rips filtration, $K_i = \mathrm{VR}_{\epsilon_i}(X)$ for an increasing sequence $0 = \epsilon_0 < \epsilon_1 < \cdots < \epsilon_m$. As $\epsilon$ grows, simplices are added but never removed, so topological features are **born** (when a new component, loop, or void appears) and **die** (when that feature merges with another or gets filled in).

### Birth, death, and persistence

Each topological feature $\gamma$ in dimension $k$ has:

- A **birth time** $b(\gamma)$: the scale $\epsilon$ at which the feature first appears.
- A **death time** $d(\gamma)$: the scale $\epsilon$ at which the feature is destroyed (merged or filled).
- A **persistence** (lifetime): $\ell(\gamma) = d(\gamma) - b(\gamma)$.

Features with **high persistence** reflect genuine structure in the data -- they survive across a wide range of scales. Features with **low persistence** are topological noise: they appear and disappear quickly as the filtration parameter changes.

This distinction between signal and noise is the core insight of persistent homology. It provides a principled, parameter-free way to separate meaningful structure from sampling artifacts.

### Persistence diagrams and barcodes

The output of persistent homology is typically represented as:

**Persistence diagram.** A multiset of points $(b_i, d_i) \in \mathbb{R}^2$ above the diagonal $b = d$, one for each topological feature. Long-lived features are far from the diagonal; noise clusters near it.

**Barcode.** An equivalent representation as a collection of intervals $[b_i, d_i)$, one per feature. Long bars indicate persistent features.

Both representations are **stable** under perturbations of the input data: the bottleneck distance between persistence diagrams is bounded by the Hausdorff distance between the underlying point clouds (Cohen-Steiner et al., 2007). This stability theorem is what makes persistent homology robust to noise and suitable for statistical inference.

### Computational complexity

For $N$ points in $\mathbb{R}^d$:

- The Vietoris-Rips complex can have up to $2^N$ simplices, but in practice the computation is dominated by the distance matrix ($O(N^2)$ space) and the persistence algorithm ($O(N^3)$ worst case via matrix reduction).
- The **ripser** algorithm (Bauer, 2021) exploits the Rips structure to achieve dramatic speedups in practice, computing $H_0$ and $H_1$ for thousands of points in seconds.
- Alpha complexes in low ambient dimension ($d \leq 3$) have $O(N^{\lceil d/2 \rceil})$ simplices and are faster, but require coordinates (not just distances).

For our dataset ($N \approx 1000$--$3000$ points in $\mathbb{R}^6$), Vietoris-Rips via ripser is tractable on a laptop.

## Why TDA for the disk archeology problem?

The forward map $F: D \to A$ from disk initial conditions to planetary system architectures is a complex, nonlinear, many-to-one function defined implicitly through population synthesis simulations. Understanding the **inverse problem** -- recovering $D$ from observations in $A$ -- requires characterizing the structure of both the image $\mathrm{im}(F)$ and the fibers $F^{-1}(y)$.

### Limitations of the KDE-on-marginals approach

Chaparro Molano et al. (2019) study the inverse problem by computing **kernel density estimates on 1D and 2D marginal projections** of the simulation output (center of mass vs. stellar mass, metallicity distributions, disk mass posteriors). This approach has fundamental limitations:

1. **Marginals discard joint structure.** Two distributions can have identical 1D and 2D marginals but completely different higher-dimensional topology. A ring and a disk in $\mathbb{R}^2$ have the same marginals on each axis, but $\beta_1 = 1$ vs. $\beta_1 = 0$.

2. **KDE is local and geometric.** It estimates the density function, which is a geometric (metric-dependent) quantity. It cannot detect **topological** features like disconnected components at different density levels, non-contractible loops, or multi-modality in high dimensions without an exponential grid.

3. **No fiber analysis.** KDE on the output space tells us where architectures cluster, but says nothing about the **preimage structure** -- whether a given architecture can arise from one or many distinct formation histories.

### What TDA adds

Persistent homology addresses each of these limitations:

| Question                                                              | KDE-on-marginals                             | Persistent homology                                                                                                             |
| --------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| How many distinct formation channels exist?                           | Counts modes in 1D/2D projections            | $H_0$: counts connected components in the full space, robust to density variations                                              |
| Are there irreducible degeneracies in the inverse problem?            | Cannot detect                                | $H_1$: non-trivial loops indicate topologically distinct families of initial conditions mapping to the same architecture region |
| Does the perturbation amplitude $A$ change the qualitative structure? | Compare overlaid density curves              | Compare Betti numbers and persistence diagrams; a change in $\beta_k$ is a **topological bifurcation**                          |
| What is the intrinsic dimensionality of the outcome space?            | Not addressed                                | Combine with manifold learning to estimate the rank of $\mathrm{im}(F)$                                                         |
| Are results coordinate-dependent?                                     | Yes (depends on which marginals are plotted) | No (homology is a topological invariant)                                                                                        |

### The fiber topology perspective

The most distinctive contribution of TDA to this problem is the ability to study the **topology of fibers** $F^{-1}(y)$. For a given observed planetary architecture $y \in A$:

- If $F^{-1}(y)$ is **connected** ($\beta_0 = 1$), the inverse problem is well-posed in the sense that all consistent initial conditions form a single family, and the degeneracy is merely parametric (a connected region of uncertainty).
- If $F^{-1}(y)$ has **multiple connected components** ($\beta_0 > 1$), the inverse problem is fundamentally degenerate: there are genuinely distinct formation histories that produce indistinguishable outcomes, and no amount of improved measurement precision (within the current observable set) can resolve them.

This distinction has direct observational consequences: if the fiber is disconnected, we need **qualitatively new observables** (not just better measurements of existing ones) to break the degeneracy.

### Stability and robustness

A practical concern with any analysis of simulation output is sensitivity to the specific sample and to choices of summary statistics. Persistent homology offers two guarantees:

1. **Stability theorem** (Cohen-Steiner et al., 2007): small perturbations of the input point cloud produce small changes in the persistence diagram (in the bottleneck distance). This means that persistence features with high lifetime are not artifacts of a particular Monte Carlo realization.

2. **Coordinate-freeness**: homology groups depend only on the topology of the space, not on the coordinates used to describe it. Choosing different consolidated quantities (e.g., median mass instead of mean mass) changes the geometry but preserves features that are topologically robust.

These properties make TDA a natural complement to density-based methods: KDE tells us "where" and "how much," while persistent homology tells us "how connected" and "how many distinct pieces."

## Software

The `topo-archeo` package wraps the following libraries for use in this project:

| Library                                              | Purpose                                         | Reference            |
| ---------------------------------------------------- | ----------------------------------------------- | -------------------- |
| [ripser](https://ripser.scikit-tda.org/)             | Vietoris-Rips persistent homology               | Bauer (2021)         |
| [giotto-tda](https://giotto-ai.github.io/gtda-docs/) | Sklearn-compatible TDA pipelines                | Tauzin et al. (2021) |
| [gudhi](https://gudhi.inria.fr/)                     | Alpha complexes, Rips complexes, persistence    | Maria et al. (2014)  |
| [persim](https://persim.scikit-tda.org/)             | Persistence diagram distances and visualization | Saul & Tralie (2019) |

## References

- Bauer, U. (2021). Ripser: efficient computation of Vietoris-Rips persistence barcodes. _Journal of Applied and Computational Topology_, 5, 391--423.
- Carlsson, G. (2009). Topology and data. _Bulletin of the American Mathematical Society_, 46(2), 255--308.
- Chaparro Molano, G., Bautista, F., & Miguel, Y. (2019). Transitional disk archeology from exoplanet population synthesis. _Proc. IAU Symposium_, 345. arXiv:1901.07078.
- Cohen-Steiner, D., Edelsbrunner, H., & Harer, J. (2007). Stability of persistence diagrams. _Discrete & Computational Geometry_, 37(1), 103--120.
- Edelsbrunner, H., & Harer, J. (2010). _Computational Topology: An Introduction_. American Mathematical Society.
- Edelsbrunner, H., Letscher, D., & Zomorodian, A. (2002). Topological persistence and simplification. _Discrete & Computational Geometry_, 28, 511--533.
- Giusti, C., Pastalkova, E., Curto, C., & Itskov, V. (2015). Clique topology reveals intrinsic geometric structure in neural correlations. _PNAS_, 112(44), 13455--13460.
- Hensel, F., Moor, M., & Rieck, B. (2021). A survey of topological machine learning methods. _Frontiers in Artificial Intelligence_, 4, 681108.
- Hiraoka, Y., Nakamura, T., Hirata, A., Escolar, E.G., Matsue, K., & Nishiura, Y. (2016). Hierarchical structures of amorphous solids characterized by persistent homology. _PNAS_, 113(26), 7035--7040.
- Maria, C., Boissonnat, J.D., Glisse, M., & Yvinec, M. (2014). The Gudhi library: simplicial complexes and persistent homology. In _Proc. ICMS 2014_, LNCS 8592, 167--174.
- Niyogi, P., Smale, S., & Weinberger, S. (2008). Finding the homology of submanifolds with high confidence from random samples. _Discrete & Computational Geometry_, 39(1), 419--441.
- Rabadan, R., & Blumberg, A.J. (2019). _Topological Data Analysis for Genomics and Evolution_. Cambridge University Press.
- Tauzin, G., Lupo, U., Tunstall, L., Perez, J.B., Caorsi, M., Medina-Mardones, A., Dassatti, A., & Hess, K. (2021). giotto-tda: a topological data analysis toolkit for machine learning and data exploration. _JMLR_, 22(39), 1--6.
- Xu, X., Cisewski-Kehe, J., Green, S.B., & Nagai, D. (2019). Finding cosmic voids and filament loops using topological data analysis. _Astronomy and Computing_, 27, 34--52.
- Zomorodian, A., & Carlsson, G. (2005). Computing persistent homology. _Discrete & Computational Geometry_, 33(2), 249--274.
