# **Agentic AI-Enhanced Digital Twin: Reproducible Synthetic Evaluation Framework**

This repository contains the **fully reproducible simulation framework** and **synthetic dataset** supporting the research study:

**“Agentic AI-Enhanced Digital Twins for Smart City Civil Infrastructure: A Secure, Autonomous and Auditable Management Framework.”**

Manuscript currently under review.

---

## **Research Objective**

This repository provides a formally defined computational framework for evaluating monitoring architectures in **smart city civil infrastructure systems**.

The study compares three operational configurations:

1. **Rule-Based Threshold Monitoring** – Static anomaly detection using predefined limits.
2. **Digital Twin (DT-Only) Monitoring** – State-synchronized twin with visualization and simulation services.
3. **DT + Agentic AI Orchestration** – Digital Twin integrated with a multi-agent Perception–Conceptualization–Action (PCA) layer and blockchain-backed provenance logging.

The objective is to evaluate response latency, mitigation success, operator workload, and decision auditability under controlled simulation conditions.

---

## **Experimental Design**

The dataset is generated via a **stochastic infrastructure degradation model** incorporating:

* Parameterized degradation dynamics
* Environmental noise perturbation
* Multi-level scenario complexity
* Configuration-dependent decision logic

### **Dataset Specifications**

* **30 independent simulation runs per configuration**
* **120 incidents per run**
* **3 scenario complexity levels** (Low, Medium, High)
* **3 monitoring configurations**
* **Total dataset size: 10,800 incident records**

[
3 \text{ configurations} \times 30 \text{ runs} \times 120 \text{ incidents} = 10,800
]

---

## **Dataset Structure**

File:

`synthetic_agentic_dt_dataset.csv`

### **Data Dictionary**

| Column        | Description                                                  | Type        |
| ------------- | ------------------------------------------------------------ | ----------- |
| `run_id`      | Independent simulation run identifier                        | Integer     |
| `config`      | Monitoring configuration (`rules`, `dt`, `agentic`)          | Categorical |
| `incident_id` | Incident index within each run                               | Integer     |
| `complexity`  | Scenario complexity (`low`, `medium`, `high`)                | Categorical |
| `latency_s`   | Detection latency (seconds)                                  | Float       |
| `success`     | Mitigation success indicator (1 = successful plan generated) | Boolean     |
| `workload`    | Operator workload (decisions per hour)                       | Float       |
| `justified`   | Blockchain-anchored provenance indicator                     | Boolean     |
| `alpha`       | Degradation coefficient sampled per run                      | Float       |
| `noise_sigma` | Environmental noise parameter sampled per run                | Float       |

This structure enables full recomputation of all reported statistics.

---

## **Statistical Validation Compatibility**

The dataset supports:

* Mean ± standard deviation computation
* 95% confidence interval estimation
* Paired t-tests and non-parametric alternatives
* Effect size estimation (Cohen’s d)
* Two-way ANOVA (Configuration × Complexity)
* Sensitivity analysis over degradation and noise parameters

All run-level raw data are provided to ensure compliance with open-data and reproducibility standards.

---

## **Reproducibility Protocol**

### **Environment Requirements**

* Python 3.10+
* Dependencies listed in `requirements.txt`

### **Repository Structure**

```
/agentic-dt-framework
    /data
        synthetic_agentic_dt_dataset.csv
    /scripts
        simulation.py
        analysis.py
    requirements.txt
    README.md
```

### **Dataset Regeneration**

The simulation uses a fixed global random seed:

**Random Seed: 42**

To regenerate the dataset:

```bash
pip install -r requirements.txt
python simulation.py
```

The regenerated dataset will exactly match the archived version.

---

## **Methodological Transparency**

This repository provides:

* Explicit stochastic model definitions
* Parameter sampling strategy
* Configuration-dependent performance logic
* Full raw outputs for all simulation runs
* Deterministic reproducibility via fixed seed

The framework is designed to enable independent verification and secondary statistical analysis.

---

## **Citation**

If this dataset or framework is used in academic work, please cite:

Akarma, A. (2026). *Agentic AI-Enhanced Digital Twins for Smart City Civil Infrastructure: A Secure, Autonomous and Auditable Management Framework.* Manuscript under review.

BibTeX entry:

```bibtex
@article{akarma2026agentic,
  title={Agentic AI-Enhanced Digital Twins for Smart City Civil Infrastructure},
  author={Akarma, Ali},
  year={2026},
  note={Manuscript under review},
  url={https://github.com/YourUsername/agentic-dt-framework}
}
```

---

## **License**

This project is released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

You are free to share and adapt the material provided appropriate credit is given.

---

* Add professional shields (Python, License, DOI)
* Or refine the repository structure further for maximum CV impact
