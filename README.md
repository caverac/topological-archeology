# Topological Archeology

**Persistent homology of the protoplanetary disk inverse problem.**

> **[Read the full documentation](https://caverac.github.io/topological-archeology/)**

Can we recover the primordial properties of a protoplanetary disk from the architecture of the planetary system it produced? This **archeology question** is an inverse problem: given an observed exoplanetary system, characterize the space of initial conditions that could have formed it.

This project applies **persistent homology** and **manifold learning** to the output of population synthesis simulations, replacing the KDE-on-marginals approach of [Chaparro Molano et al. (2019)](https://arxiv.org/abs/1901.07078) with topological data analysis to detect formation channels, quantify degeneracies, and identify bifurcations in the disk-to-planets forward map.

## Table of Contents

- [Packages](#packages)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Experiments CLI](#experiments-cli)
- [License](#license)

## Packages

This is a monorepo with five packages:

| Package                                     | Description                                                                                  |
| ------------------------------------------- | -------------------------------------------------------------------------------------------- |
| [`topo-archeo`](packages/topo-archeo)       | Core Python library -- TDA tools for planetary architecture analysis                         |
| [`disk-evolution`](packages/disk-evolution) | Semi-analytic planet formation model ([Miguel et al. 2011](https://arxiv.org/abs/1106.3281)) |
| [`experiments`](packages/experiments)       | Research CLI for running simulations and generating figures                                  |
| [`docs`](packages/docs)                     | Project documentation ([live site](https://caverac.github.io/topological-archeology/))       |
| [`infrastructure`](packages/infrastructure) | AWS CDK stacks for large-scale parallel simulation on Lambda                                 |

## Getting Started

This project uses [mise](https://mise.jdx.dev/) to manage tool versions (Node 22, Python 3.14, uv).

```bash
# Install tool versions
mise install

# Install JS/TS dependencies
yarn install

# Install Python dependencies
uv sync --all-groups
```

## Documentation

All details about the simulation model, validation results, and TDA methodology live on the [documentation site](https://caverac.github.io/topological-archeology/). To run it locally:

```bash
yarn workspace @topo-archeo/docs start
```

## Experiments CLI

The `experiments` package provides a CLI for running population synthesis and analyzing results:

```bash
# Run a local population census (50 systems, no migration)
uv run experiments pop-census --n-systems 50 --gamma 1.0 --c-mig-i 0.0

# Submit 1000 jobs to AWS Lambda
uv run experiments submit --n-systems 1000 --gamma 1.0

# Collect and display results
uv run experiments collect --run-id <run-id>
```

## License

MIT
