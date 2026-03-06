<div align="center">

<!-- Hero Logo / Banner -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=14&duration=0&pause=1000&color=64B5F6&center=true&vCenter=true&repeat=false&width=700&lines=AGENTIC+AI-ENHANCED+DIGITAL+TWIN+FRAMEWORK" />
  <img alt="Project Banner" src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=14&duration=0&pause=1000&color=1565C0&center=true&vCenter=true&repeat=false&width=700&lines=AGENTIC+AI-ENHANCED+DIGITAL+TWIN+FRAMEWORK" />
</picture>

# Agentic AI-Enhanced Digital Twin
## Reproducible Synthetic Evaluation Framework

<br/>

<!-- Badges -->
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.26.4-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2.2-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![SciPy](https://img.shields.io/badge/SciPy-1.11.4-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)](https://scipy.org/)

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey?style=for-the-badge&logo=creativecommons&logoColor=white)](https://creativecommons.org/licenses/by/4.0/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18843087-blue?style=for-the-badge&logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.18843087)
[![Status](https://img.shields.io/badge/Manuscript-Under%20Review-orange?style=for-the-badge&logo=academia&logoColor=white)]()

<br/>

<img src="https://img.shields.io/badge/Smart%20City-Infrastructure-1a73e8?style=flat-square&logo=cityMapper&logoColor=white" />
<img src="https://img.shields.io/badge/Structural%20Health-Monitoring-2e7d32?style=flat-square&logo=radar&logoColor=white" />
<img src="https://img.shields.io/badge/Reproducible-Research-7b1fa2?style=flat-square&logo=jupyter&logoColor=white" />
<img src="https://img.shields.io/badge/Blockchain-Audit%20Trail-f57c00?style=flat-square&logo=ethereum&logoColor=white" />

<br/><br/>

> **Supporting repository for:**
> *"Agentic AI-Enhanced Digital Twins for Smart City Civil Infrastructure: A Secure, Autonomous and Auditable Management Framework."*
> — Manuscript under review.

---

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Configurations](#-three-configurations-evaluated)
- [Degradation Model](#-degradation-model)
- [Parameter Calibration](#parameter-calibration)
- [Detection Mechanisms](#-detection-mechanisms)
- [Mitigation Success Model](#-mitigation-success-model)
- [Pipeline Latency Model](#-pipeline-latency-model)
- [Dataset Specifications](#-dataset-specifications)
- [Statistical Analysis](#-statistical-analysis)
- [Reproducibility Protocol](#-reproducibility-protocol)
- [References](#-references)
- [License](#-license)

---

## 🔭 Overview

This repository provides a **fully reproducible simulation framework** and synthetic dataset for evaluating monitoring architectures in smart city civil infrastructure systems.

> Unlike parameter-table approaches, **performance in this framework emerges from the physics-grounded simulation mechanics** — detection latency and mitigation success are computed outcomes, not pre-assigned distributions.

---

## ⚙️ Three Configurations Evaluated

| ID | Configuration | Detection Mechanism |
|:---:|---|---|
| `rules` | **Rule-Based Threshold Monitoring** | Static threshold crossing on noisy sensor stream |
| `dt` | **Digital Twin (DT-Only)** | Kalman-filtered state estimation with predictive horizon alert |
| `agentic` | **DT + Agentic AI Orchestration** | Adaptive Bayesian threshold with shock-context adjustment and multi-step lookahead |

---

## 📐 Degradation Model

Each incident is generated from a **discrete-time stochastic degradation process**:

$$D(t) = D(t-1) + \alpha \cdot D(t-1) + S(t)$$

| Symbol | Definition |
|---|---|
| `D(t) ∈ [0, 1]` | Structural degradation index at timestep `t` |
| `α ~ N(α_mean, α_std)` | Per-run exponential drift coefficient representing fatigue accumulation *(Paris & Erdogan, 1963; AASHTO LRFD, 2020)* |
| `S(t)` | Poisson-gated shock: `S(t) = max(N(μ_s, σ_s), 0)` with probability `λ_shock` per step, else `S(t) = 0` |

The simulation runs at **Δt = 0.1 hr** resolution. Sensor observations are corrupted by Gaussian noise `ε ~ N(0, 0.02²)`, consistent with commercial strain gauge SHM systems *(e.g., HBM QuantumX noise floor specifications)*.

### Parameter Calibration

Degradation rates are calibrated to produce timescales of **20–200 hours**, consistent with observed fatigue crack growth rates in steel bridge members:

| Complexity | `α_mean` | `λ_shock` | `μ_shock` | Reference |
|:---:|:---:|:---:|:---:|---|
| 🟢 Low | `0.0030` | `0.010` | `0.040` | Mori & Ellingwood (1994) |
| 🟡 Medium | `0.0060` | `0.030` | `0.080` | Frangopol et al. (2004) |
| 🔴 High | `0.0120` | `0.060` | `0.120` | Strauss et al. (2008) |

---

## 🔍 Detection Mechanisms

### 📏 Rules-Based

Generates an alarm when the noisy sensor reading first exceeds a **static threshold `τ_rules = 0.70`**. This threshold approximates recommended intervention levels in standard infrastructure condition indices *(e.g., FHWA bridge condition rating)*.

---

### 🔄 Digital Twin

Implements a **scalar Kalman filter** *(Kalman, 1960)* tracking the structural state:

```
Prediction:  x̂⁻(t) = x̂(t-1)·(1 + α̂),    P⁻(t) = P(t-1) + Q
Update:      K(t) = P⁻(t) / (P⁻(t) + R),  x̂(t) = x̂⁻(t) + K·(z(t) − x̂⁻(t))
```

An alert fires when the **projected state 15 steps ahead (1.5 hours)** exceeds `τ_DT = 0.70`.

---

### 🤖 Agentic AI

The agentic layer maintains a Kalman estimate *and* a **shock-context memory**. The adaptive threshold is:

```
τ_agentic(t) = max(τ_base − 0.04 · N_shocks(t, window=20), 0.30)
```

where `N_shocks(t, window=20)` counts Poisson shocks detected within the last 20 timesteps. This models a **PCA (Perception–Conceptualization–Action) agent** that elevates sensitivity following adverse contextual signals, consistent with Endsley's (1995) Situation Awareness model applied to autonomous infrastructure agents.

---

## ✅ Mitigation Success Model

Mitigation success is **not pre-assigned**. For each incident, a Bernoulli trial is drawn with probability:

$$P(\text{success}) = \sigma\!\left(-2.0 + 0.8 \cdot \text{margin\_hours}\right)$$

where `margin_hours` = time from detection to projected critical failure (`D ≥ 0.85`), and `σ(·)` is the logistic function.

| Detection Margin | P(success) | Outcome |
|:---:|:---:|:---:|
| 0 hr | ~11% | 🔴 Critical |
| 2.5 hr | ~50% | 🟡 Marginal |
| 5.0 hr | ~88% | 🟢 Good |
| 7.5 hr | ~96% *(capped at 95%)* | 🟢 Excellent |

> **Earlier detection → longer margin → higher success probability.** Performance differences across configurations emerge directly from this mechanism.

---

## ⏱️ Pipeline Latency Model

Algorithmic detection time is augmented by **operator/system pipeline latency (seconds)**, derived from human factors analysis of control room workflows *(Hart & Staveland, 1988; NASA-TLX)*:

| Configuration | Pipeline Mean (s) | Pipeline SD (s) | Workflow Description |
|:---:|:---:|:---:|---|
| `rules` | 42 | 8 | Sensor alert → manual dashboard review → phone dispatch |
| `dt` | 18 | 4 | Automated alert → operator screen confirmation → dispatch |
| `agentic` | 6 | 2 | Autonomous plan generation → push notification → dispatch |

> **Total latency** = algorithmic detection delay + pipeline latency.

---

## 📊 Dataset Specifications

> **File:** `data/synthetic_agentic_dt_dataset.csv`

```
3 configurations × 30 runs × 120 incidents = 10,800 incident records
```

### Data Dictionary

| Column | Description | Type |
|---|---|:---:|
| `run_id` | Independent simulation run (0–29) | `Integer` |
| `config` | Configuration (`rules`, `dt`, `agentic`) | `Categorical` |
| `incident_id` | Incident index within run (0–119) | `Integer` |
| `complexity` | Scenario complexity (`low`, `medium`, `high`) | `Categorical` |
| `latency_s` | Total detection + pipeline latency (seconds) | `Float` |
| `success` | Mitigation success (1 = successful plan executed) | `Boolean` |
| `workload` | Operator workload (decisions/hour) | `Float` |
| `justified` | Blockchain-anchored audit trail present | `Boolean` |
| `alpha` | Per-run degradation drift coefficient | `Float` |
| `noise_sigma` | Shock magnitude noise parameter | `Float` |

---

## 📈 Statistical Analysis

The analysis script (`scripts/analysis.py`) produces a comprehensive battery of tests:

| # | Method | Purpose |
|:---:|---|---|
| 1 | **Descriptive Statistics** | Mean, SD, 95% CI per config × complexity |
| 2 | **Shapiro-Wilk Test** | Normality screening with non-parametric fallback |
| 3 | **Welch's t-tests** | Pairwise latency comparisons with Bonferroni correction |
| 4 | **Mann-Whitney U** | Non-parametric complement with rank-biserial `r` |
| 5 | **Chi-squared Tests** | Pairwise mitigation success rate comparisons |
| 6 | **Two-way ANOVA** | Type II SS — Config × Complexity for latency and success |
| 7 | **Tukey HSD Post-hoc** | All pairwise group comparisons |
| 8 | **Effect Sizes** | Cohen's d (parametric) and rank-biserial r (non-parametric) |
| 9 | **Sensitivity Analysis** | Spearman ρ of α and σ with outcomes |
| 10 | **Run-level Aggregation** | Table 1 format for manuscript reporting |

---

## 🔁 Reproducibility Protocol

### 🐍 Environment

```
Python       3.10+
numpy        1.26.4
pandas       2.2.2
scipy        1.11.4
statsmodels  0.14.1
```

### 🗂️ Repository Structure

```
agentic-dt-framework/
├── 📁 data/
│   └── synthetic_agentic_dt_dataset.csv
├── 📁 scripts/
│   ├── simulation.py
│   └── analysis.py
├── requirements.txt
└── README.md
```

### 🚀 Run

```bash
# Install dependencies
pip install -r requirements.txt

# Regenerate dataset (deterministic, seed=42)
cd scripts
python simulation.py

# Run full statistical analysis
python analysis.py
```

> ✅ The regenerated dataset is **guaranteed to exactly match** the archived version (seed=42).

---

## 📚 References

<details>
<summary><strong>Click to expand full reference list</strong></summary>

<br/>

- **Endsley, M.R.** (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors*, 37(1), 32–64.
- **Farrar, C.R. & Worden, K.** (2012). *Structural Health Monitoring: A Machine Learning Perspective*. Wiley.
- **Frangopol, D.M., et al.** (2004). Maintenance, monitoring, safety, risk and resilience of deteriorating systems. *J. Struct. Eng.*
- **Hart, S.G. & Staveland, L.E.** (1988). Development of NASA-TLX. *Human Mental Workload*, 1, 139–183.
- **Kalman, R.E.** (1960). A new approach to linear filtering and prediction problems. *J. Basic Eng.*, 82(1), 35–45.
- **Mori, Y. & Ellingwood, B.R.** (1994). Maintaining reliability of concrete structures. *J. Struct. Eng.*, 120(3), 824–845.
- **Paris, P. & Erdogan, F.** (1963). A critical analysis of crack propagation laws. *J. Basic Eng.*, 85(4), 528–533.
- **Strauss, A., et al.** (2008). Stochastic finite elements and experimental investigations of the durability of concrete structures. *Structural Safety*, 30(5), 380–395.

</details>

---

## 📄 License

<div align="center">

Released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

[![CC BY 4.0](https://licensebuttons.net/l/by/4.0/88x31.png)](https://creativecommons.org/licenses/by/4.0/)

You are free to **share** and **adapt** the material provided appropriate credit is given.

<br/>

---

<sub>Built with ❤️ for reproducible civil infrastructure research · DOI: <a href="https://doi.org/10.5281/zenodo.18843087">10.5281/zenodo.18843087</a></sub>

</div>
