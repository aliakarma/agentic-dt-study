Agentic AI-Enhanced Digital Twin: Reproducible Synthetic Evaluation Framework

This repository contains the complete reproducible computational framework and synthetic dataset supporting the manuscript:

Agentic AI-Enhanced Digital Twins for Smart City Civil Infrastructure: A Secure, Autonomous and Auditable Management Framework

Submitted to PLOS ONE.

Research Scope

This repository provides a fully specified and reproducible synthetic evaluation framework for assessing monitoring configurations in smart city civil infrastructure systems.

The study evaluates three operational configurations:

Rule-based threshold monitoring

Digital Twin–assisted monitoring

Digital Twin integrated with Agentic AI orchestration and blockchain-backed provenance

The objective is to quantitatively evaluate latency, intervention success rate, operator workload, and decision auditability under controlled stochastic conditions.

Experimental Design

The dataset is generated via a formally defined stochastic simulation model incorporating:

Infrastructure degradation dynamics

Environmental noise perturbation

Scenario complexity stratification

Configuration-dependent response behavior

Each configuration is evaluated across:

30 independent simulation runs

120 incidents per run

3 scenario complexity levels (low, medium, high)

Total dataset size:

3 configurations × 30 runs × 120 incidents = 10,800 incident records

The simulation includes controlled parameter variation to support sensitivity analysis.

Dataset Structure

File:

synthetic_agentic_dt_dataset.csv

Columns:

run_id — independent simulation run identifier

config — monitoring configuration (rules, dt, agentic)

incident_id — incident index within run

complexity — scenario complexity level

latency_s — anomaly detection latency (seconds)

success — binary mitigation generation indicator

workload — operator workload (decisions per hour)

justified — binary blockchain-anchored provenance indicator

alpha — degradation coefficient sampled for run

noise_sigma — environmental noise parameter

The dataset contains raw run-level outputs and supports full recomputation of:

Mean and standard deviation

95% confidence intervals

Paired statistical tests

Effect size estimation

Two-way ANOVA

Sensitivity analysis

Reproducibility Protocol

Random seed: 42

To regenerate the dataset exactly:

Install dependencies:

pip install -r requirements.txt

Execute the simulation:

python simulation.py

The regenerated dataset will match the archived dataset deterministically.

All numerical values reported in the manuscript are directly derived from this dataset.

Computational Dependencies

Python 3.10+

NumPy

Pandas

SciPy

Exact versions are specified in requirements.txt.

Transparency and Data Policy Compliance

This repository provides the minimal dataset required to replicate all reported findings, including:

Raw simulation outputs

Parameter configurations

Stochastic sampling metadata

Deterministic seed specification

The archive is intended to satisfy PLOS ONE’s open data and reproducibility requirements.

Upon publication, a DOI-backed archival version will be provided via Zenodo.

License

This repository and associated dataset are released under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
