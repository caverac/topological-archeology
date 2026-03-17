---
slug: /
sidebar_position: 1
---

# Introduction

## The archeology question

Every exoplanetary system we observe today is the end product of a formation process that unfolded over millions of years inside a protoplanetary disk. The disk is long gone, but its fingerprints remain in the masses, orbits, and multiplicities of the surviving planets. **Disk archeology** asks: can we read those fingerprints backward -- can we recover properties of the primordial disk from the architecture of the planetary system it produced?

This is an **inverse problem**. The forward direction -- disk evolves into planets -- is handled by population synthesis models that simulate core accretion, gas accretion, migration, and collisions across thousands of Monte Carlo realizations ([Miguel, Guilera & Brunini, 2011](https://arxiv.org/abs/1106.3281); [Benz et al., 2014](https://arxiv.org/abs/1402.7086)). The result is a map

$$
F: \mathcal{D} \to \mathcal{A}
$$

from the space of disk initial conditions $\mathcal{D}$ (stellar mass, disk mass, metallicity, radial extent, gas dissipation timescale) to the space of planetary system architectures $\mathcal{A}$ (planet counts, masses, orbital distribution).

The inverse direction -- given an observed architecture $y \in \mathcal{A}$, characterize the **preimage fiber** $F^{-1}(y) \subset \mathcal{D}$ -- is where the difficulty lies. Here $F^{-1}(y)$ denotes the preimage set $\{x \in \mathcal{D} : F(x) = y\}$, not a functional inverse, which does not exist since $F$ is many-to-one. The map $F$ is nonlinear, stochastic, and many-to-one. Multiple disk configurations can produce indistinguishable planetary systems.

## Transitional disks and the perturbation question

Not all protoplanetary disks are smooth. Observations with ALMA and other facilities have revealed a class of **transitional disks** with gaps, cavities, and radial density perturbations ([van der Marel et al., 2015](https://doi.org/10.1051/0004-6361/201526684)). These inhomogeneities may arise from embedded planets, pressure bumps, or photoevaporation, and they create **dust traps** that alter the local conditions for planet formation ([Pinilla et al., 2012](https://doi.org/10.1051/0004-6361/201116882)).

[Chaparro Molano, Bautista & Miguel (2019)](https://arxiv.org/abs/1901.07078) investigated the impact of such perturbations on planetary populations by running 3000+ population synthesis simulations with a radial density perturbation superimposed on the disk profile:

$$
\Sigma_p(r) = \Sigma(r)\left[1 + A\cos\left(\frac{2\pi r}{f\,H(r)}\right)\right]
$$

where $A = 0$ gives a smooth disk and $A = 0.3$ represents a transitional disk. Their key finding: transitional disks favor the formation of giant planets at lower disk masses than smooth disks. They studied this through KDE-smoothed marginal posteriors -- 1D and 2D projections of the simulation output.

## Beyond marginals: a topological perspective

The Bayesian framework of Chaparro Molano et al. (2019) successfully establishes the link between disk properties and planetary populations through KDE-smoothed posteriors. Their results -- that transitional disks favor giant planet formation, that synthetic and observed populations overlap in stellar mass vs. center of mass space -- provide the empirical foundation this project builds on.

We extend their analysis by bringing tools from **algebraic topology** to bear on the same data. Where density estimation characterizes the _geometry_ of the population (where systems cluster, how distributions shift), persistent homology characterizes its _topology_ (how many distinct clusters exist, whether the space has non-trivial loops or voids). These are complementary perspectives:

1. **Full-dimensional structure.** Marginal projections are natural for visualization and interpretation, but the archeology inverse problem lives in the joint space of all consolidated quantities simultaneously. Topological invariants computed on the full point cloud can detect structure that no single 2D projection reveals.

2. **Fiber topology.** Density estimates on the output space $\mathcal{A}$ tell us where planetary architectures cluster. Persistent homology on the preimage $F^{-1}(y)$ additionally tells us whether a given architecture can arise from one or many **topologically distinct** formation histories -- a question that directly quantifies the degeneracy of the inverse problem.

3. **Qualitative transitions.** Comparing density curves for $A = 0$ and $A = 0.3$ reveals quantitative shifts. Tracking [Betti numbers](tda/preliminaries#homology-groups) (integer counts of connected components, loops, and voids) across a sweep of $A$ values can additionally detect **topological bifurcations** -- critical thresholds where the qualitative structure of the outcome space changes.

## Our approach: Topological Data Analysis

This project extends the population synthesis framework of Chaparro Molano et al. with **persistent homology** and **manifold learning** applied to the full parameter space. The goal is to determine whether the archeology inverse problem has a well-defined topological structure -- or whether there are irreducible degeneracies that demand new observables.

The approach unfolds in four phases:

### Phase A: Persistent homology of the outcome space

Apply Vietoris-Rips persistent homology to the point cloud of simulated planetary architectures in $\mathbb{R}^6$. The persistence diagram reveals:

- **$H_0$ (connected components)**: distinct formation channels beyond the binary giant/terrestrial split.
- **$H_1$ (loops)**: non-trivial cycles indicating regions where the inverse problem is fundamentally ill-posed -- topologically distinct families of initial conditions map to the same architecture neighborhood.

See [Persistent Homology](tda/persistence) for results.

### Phase B: Manifold learning on the forward map

Use UMAP, diffusion maps, or spectral methods to embed $\mathcal{D}$ and $\mathcal{A}$ separately, then study the induced map between embeddings. Estimate the **intrinsic dimension** of $\mathrm{im}(F)$ -- the hypothesis is that the dissipative dynamics of disk evolution collapses the 5-dimensional input onto a 2- or 3-dimensional effective manifold of accessible architectures.

### Phase C: Fiber analysis of the inverse problem

For selected observed systems, identify the preimage neighborhood $F^{-1}(B_\epsilon(y))$ in the simulation data and compute $H_0$ persistence on the fibers. Connected fibers ($\beta_0 = 1$) mean the inverse problem is well-posed; disconnected fibers ($\beta_0 > 1$) indicate genuinely distinct formation histories consistent with the same observables.

### Phase D: Bifurcation detection via persistence

Sweep the perturbation amplitude $A$ from 0 to 0.3 in fine steps and track persistence diagrams at each value. A **topological bifurcation** -- a feature that is born or dies as $A$ crosses a critical threshold -- reveals whether the smooth-to-transitional transition is a gradual reshaping or a sharp phase transition in formation outcomes.

See [Bifurcation Analysis](tda/bifurcation) for results.

## Project structure

This is a monorepo with four packages:

| Package                                                                                                | Description                                                               |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| [`disk-evolution`](https://github.com/cavera/topological-archeology/tree/main/packages/disk-evolution) | Semi-analytic planet formation simulator (TypeScript, runs on AWS Lambda) |
| [`topo-archeo`](https://github.com/cavera/topological-archeology/tree/main/packages/topo-archeo)       | TDA analysis library (Python: ripser, giotto-tda, UMAP)                   |
| [`experiments`](https://github.com/cavera/topological-archeology/tree/main/packages/experiments)       | CLI for submitting simulation runs and running analyses                   |
| [`docs`](https://github.com/cavera/topological-archeology/tree/main/packages/docs)                     | This documentation site (Docusaurus)                                      |

## Key references

- Chaparro Molano, G., Bautista, F., & Miguel, Y. (2019). Transitional disk archeology from exoplanet population synthesis. _Proc. IAU Symposium_, 345. [arXiv:1901.07078](https://arxiv.org/abs/1901.07078).
- Miguel, Y., Guilera, M., & Brunini, A. (2011). The diversity of planetary system architectures. _MNRAS_, 417, 314. [arXiv:1106.3281](https://arxiv.org/abs/1106.3281).
- Benz, W., Ida, S., Alibert, Y., Lin, D.N.C., & Mordasini, C. (2014). Planet population synthesis. In _Protostars and Planets VI_, 691--713. [arXiv:1402.7086](https://arxiv.org/abs/1402.7086).
- Pinilla, P., Birnstiel, T., Ricci, L., et al. (2012). Trapping dust particles in the outer regions of protoplanetary disks. _A&A_, 538, A114.
- Carlsson, G. (2009). Topology and data. _Bull. Amer. Math. Soc._, 46(2), 255--308.
- Edelsbrunner, H. & Harer, J. (2010). _Computational Topology: An Introduction_. AMS.
