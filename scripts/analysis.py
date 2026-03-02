import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Load dataset
df = pd.read_csv("../data/synthetic_agentic_dt_dataset.csv")

# -----------------------------
# Descriptive Statistics
# -----------------------------
print("\n=== Descriptive Statistics (Latency) ===")
desc = df.groupby("config")["latency_s"].agg(["mean","std"])
desc["ci_95"] = 1.96 * desc["std"] / np.sqrt(3600)
print(desc)

# -----------------------------
# T-Tests
# -----------------------------
print("\n=== T-Tests (Latency) ===")
rules = df[df["config"]=="rules"]["latency_s"]
dt = df[df["config"]=="dt"]["latency_s"]
agentic = df[df["config"]=="agentic"]["latency_s"]

print("Agentic vs DT:", ttest_ind(agentic, dt))
print("Agentic vs Rules:", ttest_ind(agentic, rules))
print("DT vs Rules:", ttest_ind(dt, rules))

# -----------------------------
# Effect Sizes
# -----------------------------
def cohens_d(a, b):
    diff = a.mean() - b.mean()
    pooled_sd = np.sqrt((a.std()**2 + b.std()**2)/2)
    return diff / pooled_sd

print("\n=== Effect Sizes (Cohen's d) ===")
print("Agentic vs DT:", cohens_d(agentic, dt))
print("Agentic vs Rules:", cohens_d(agentic, rules))
print("DT vs Rules:", cohens_d(dt, rules))

# -----------------------------
# Two-Way ANOVA (Latency)
# -----------------------------
print("\n=== Two-Way ANOVA (Latency) ===")
df["config"] = df["config"].astype("category")
df["complexity"] = df["complexity"].astype("category")

model_latency = ols("latency_s ~ C(config) + C(complexity) + C(config):C(complexity)", data=df).fit()
anova_latency = sm.stats.anova_lm(model_latency, typ=2)
print(anova_latency)

# -----------------------------
# Two-Way ANOVA (Success)
# -----------------------------
print("\n=== Two-Way ANOVA (Success) ===")
model_success = ols("success ~ C(config) + C(complexity) + C(config):C(complexity)", data=df).fit()
anova_success = sm.stats.anova_lm(model_success, typ=2)
print(anova_success)
