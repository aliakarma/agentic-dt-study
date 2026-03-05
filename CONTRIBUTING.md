# Contributing to agentic-dt-study

Thank you for your interest in contributing to this research repository supporting our PLOS ONE publication. This project prioritizes **reproducibility**, **transparency**, and **scientific rigor**.

## 🎯 Scope of Contributions
We welcome:
- Bug fixes and performance improvements to `simulation.py` or `analysis.py`
- Enhanced documentation, tutorials, or visualization examples
- Extensions to the synthetic data generator (with clear methodological justification)
- Statistical validation enhancements or alternative analysis approaches
- Accessibility improvements (e.g., containerization, cloud deployment guides)

We do *not* accept:
- Changes that break reproducibility of the published results (see "Reproducibility Guardrails" below)
- Unsubstantiated modifications to the core physics-based degradation model
- License-incompatible code or data additions

## 🚀 Getting Started

### Prerequisites
- Python ≥ 3.9
- Git
- Virtual environment tool (`venv`, `conda`, or `virtualenv`)

### Setup Instructions
```bash
# 1. Fork and clone the repository
git clone https://github.com/aliakarma/agentic-dt-study.git
cd agentic-dt-study

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify reproducibility (should match paper results)
python simulation.py --seed 42
python analysis.py --input data/synthetic_agentic_dt_dataset.csv
