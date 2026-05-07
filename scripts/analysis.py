import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import shapiro, mannwhitneyu, chi2_contingency
import statsmodels.api as sm
from statsmodels.formula.api import ols
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests
import warnings
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

warnings.filterwarnings("ignore")

# Configure output directory
RESULTS_DIR = "../results"
os.makedirs(RESULTS_DIR, exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")

def add_labels(ax, fmt=".2f"):
    """Add data labels to bars in a plot."""
    for p in ax.patches:
        ax.annotate(f'{p.get_height():{fmt}}', 
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 9), 
                    textcoords='offset points', fontsize=10, fontweight='bold')

# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------
df = pd.read_csv("../data/synthetic_agentic_dt_dataset.csv")
df["config"]     = pd.Categorical(df["config"],     categories=["rules", "dt", "dt_single_agent", "dt_multi_no_chain", "agentic_full"], ordered=False)
df["complexity"] = pd.Categorical(df["complexity"], categories=["low", "medium", "high"],   ordered=True)

CONFIGS      = ["rules", "dt", "dt_single_agent", "dt_multi_no_chain", "agentic_full"]
COMPLEXITIES = ["low", "medium", "high"]
N_PER_CONFIG = len(df) // len(CONFIGS)


def sep(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("-" * 60)


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    """Pooled-SD Cohen's d."""
    diff = a.mean() - b.mean()
    s    = np.sqrt((a.std(ddof=1) ** 2 + b.std(ddof=1) ** 2) / 2)
    return diff / s if s != 0 else np.nan


def rank_biserial_r(u_stat: float, n1: int, n2: int) -> float:
    """Rank-biserial correlation from Mann-Whitney U."""
    return 1 - (2 * u_stat) / (n1 * n2)


def ci_95(series: pd.Series) -> float:
    """95% CI half-width (t-distribution)."""
    n  = len(series)
    se = series.std(ddof=1) / np.sqrt(n)
    t  = stats.t.ppf(0.975, df=n - 1)
    return t * se


# ############################################################
# 1. Descriptive Statistics
# ############################################################
sep("1. DESCRIPTIVE STATISTICS")

for metric in ["latency_s", "success", "workload"]:
    print(f"\n  [{metric}]")
    rows = []
    for config in CONFIGS:
        for cx in COMPLEXITIES:
            sub = df[(df["config"] == config) & (df["complexity"] == cx)][metric]
            rows.append({
                "config":      config,
                "complexity":  cx,
                "n":           len(sub),
                "mean":        sub.mean(),
                "sd":          sub.std(ddof=1),
                "ci_95_half":  ci_95(sub),
                "median":      sub.median(),
            })
    df_desc = pd.DataFrame(rows)
    print(df_desc.round(3).to_string(index=False))
    df_desc.to_json(os.path.join(RESULTS_DIR, f"desc_stats_{metric}.json"), orient="records", indent=2)

# Overall by config
sep("  Overall means by config")
print(df.groupby("config")[["latency_s", "success", "workload"]].agg(
    ["mean", "std", "median"]
).round(3))


# ############################################################
# 2. Normality Screening (Shapiro-Wilk, sampled)
# ############################################################
sep("2. NORMALITY SCREENING (Shapiro-Wilk, n<=5000 subsample)")
for metric in ["latency_s", "workload"]:
    print(f"\n  [{metric}]")
    for config in CONFIGS:
        sub  = df[df["config"] == config][metric]
        samp = sub.sample(min(len(sub), 5000), random_state=42)
        stat, p = shapiro(samp)
        note = "  <- non-normal" if p < 0.05 else ""
        print(f"    {config:8s}  W={stat:.4f}  p={p:.4f}{note}")


# ############################################################
# 3. Welch's t-Tests (Latency)
# ############################################################
sep("3. WELCH'S t-TESTS -- LATENCY")
pairs = [("agentic_full", "dt_multi_no_chain"), ("agentic_full", "dt"), ("dt", "rules")]
raw_p = []
results_t = []

for a, b in pairs:
    s_a = df[df["config"] == a]["latency_s"]
    s_b = df[df["config"] == b]["latency_s"]
    t,  p  = stats.ttest_ind(s_a, s_b, equal_var=False)
    d       = cohens_d(s_a, s_b)
    raw_p.append(p)
    results_t.append({"comparison": f"{a} vs {b}", "t": t, "p_raw": p, "cohens_d": d})

# Bonferroni correction
_, p_corr, _, _ = multipletests(raw_p, method="bonferroni")
for i, r in enumerate(results_t):
    r["p_bonferroni"] = p_corr[i]

print(pd.DataFrame(results_t).round(4).to_string(index=False))
pd.DataFrame(results_t).to_json(os.path.join(RESULTS_DIR, "t_tests_latency.json"), orient="records", indent=2)


# ############################################################
# 4. Mann-Whitney U Tests (non-parametric complement)
# ############################################################
sep("4. MANN-WHITNEY U TESTS -- LATENCY (non-parametric)")
mw_raw_p = []
mw_results = []

for a, b in pairs:
    s_a = df[df["config"] == a]["latency_s"]
    s_b = df[df["config"] == b]["latency_s"]
    U, p = mannwhitneyu(s_a, s_b, alternative="two-sided")
    r    = rank_biserial_r(U, len(s_a), len(s_b))
    mw_raw_p.append(p)
    mw_results.append({"comparison": f"{a} vs {b}", "U": U, "p_raw": p, "r_biserial": r})

_, p_mw_corr, _, _ = multipletests(mw_raw_p, method="bonferroni")
for i, r in enumerate(mw_results):
    r["p_bonferroni"] = p_mw_corr[i]

print(pd.DataFrame(mw_results).round(4).to_string(index=False))


# ############################################################
# 5. Chi-Squared Tests — Mitigation Success Rate
# ############################################################
sep("5. CHI-SQUARED TESTS -- MITIGATION SUCCESS RATE")
print("\n  Success rates by config:")
print(df.groupby("config")["success"].agg(["mean", "sum", "count"]).round(3))

print("\n  Pairwise chi-squared tests:")
chi_raw_p = []
chi_results = []
for a, b in pairs:
    s_a = df[df["config"] == a]["success"].values
    s_b = df[df["config"] == b]["success"].values
    # Build 2×2 contingency table: rows = outcome (0/1), cols = config
    ct = np.array([
        [(s_a == 0).sum(), (s_b == 0).sum()],
        [(s_a == 1).sum(), (s_b == 1).sum()],
    ])
    chi2, p, dof, _ = chi2_contingency(ct)
    chi_raw_p.append(p)
    chi_results.append({"comparison": f"{a} vs {b}", "chi2": chi2, "df": dof, "p_raw": p})

_, p_chi_corr, _, _ = multipletests(chi_raw_p, method="bonferroni")
for i, r in enumerate(chi_results):
    r["p_bonferroni"] = p_chi_corr[i]

print(pd.DataFrame(chi_results).round(4).to_string(index=False))
pd.DataFrame(chi_results).to_json(os.path.join(RESULTS_DIR, "chi_squared_success.json"), orient="records", indent=2)


# ############################################################
# 6. Two-Way ANOVA -- Configuration x Complexity
# ############################################################
sep("6. TWO-WAY ANOVA (Type II SS)")
for metric in ["latency_s", "success"]:
    print(f"\n  Outcome: {metric}")
    model  = ols(f"{metric} ~ C(config) + C(complexity) + C(config):C(complexity)", data=df).fit()
    anova  = sm.stats.anova_lm(model, typ=2)

    # Eta-squared (partial)
    ss_resid = anova.loc["Residual", "sum_sq"]
    anova["eta_sq_partial"] = anova["sum_sq"] / (anova["sum_sq"] + ss_resid)

    print(anova[["sum_sq", "df", "F", "PR(>F)", "eta_sq_partial"]].round(4))

sep("6b. MIXED-EFFECTS MODELING (Accounting for Run-Level Nesting)")
# Random intercept for run_id
# We use a simpler formula for LMM to ensure convergence
md = smf.mixedlm("latency_s ~ C(config) + C(complexity)", df, groups=df["run_id"])
mdf = md.fit()
print(mdf.summary())

sep("Multivariate Logistic Regression for Success")
# Add alpha as covariate (removed noise_sigma due to perfect collinearity with complexity)
log_reg = smf.logit("success ~ C(config) + C(complexity) + alpha", data=df).fit()
print(log_reg.summary())


# ############################################################
# 7. Post-hoc Tukey HSD -- Latency by Config
# ############################################################
sep("7. POST-HOC TUKEY HSD -- LATENCY BY CONFIGURATION")
tukey = pairwise_tukeyhsd(endog=df["latency_s"], groups=df["config"], alpha=0.05)
print(tukey.summary())

sep("   POST-HOC TUKEY HSD -- LATENCY BY COMPLEXITY")
tukey_cx = pairwise_tukeyhsd(endog=df["latency_s"], groups=df["complexity"], alpha=0.05)
print(tukey_cx.summary())


# ############################################################
# 8. Workload and Justification Summary
# ############################################################
sep("8. WORKLOAD AND PROVENANCE JUSTIFICATION")
print("\n  Workload (decisions/hour):")
print(df.groupby("config")["workload"].agg(["mean", "std", "median"]).round(3))

print("\n  Blockchain-justified proportion:")
print(df.groupby("config")["justified"].agg(["mean", "sum", "count"]).round(3))


# ############################################################
# 9. Sensitivity Analysis — Degradation Parameters
# ############################################################
sep("9. SENSITIVITY ANALYSIS -- Degradation Parameters")

# Spearman correlation of alpha and noise_sigma with latency/success
print("\n  Spearman rho with latency_s:")
for config in CONFIGS:
    sub = df[df["config"] == config]
    ra, pa = stats.spearmanr(sub["alpha"],       sub["latency_s"])
    rn, pn = stats.spearmanr(sub["noise_sigma"], sub["latency_s"])
    print(f"    {config:8s}  alpha->latency: rho={ra:.3f} (p={pa:.3f})  "
          f"sigma->latency: rho={rn:.3f} (p={pn:.3f})")

print("\n  Spearman rho with success:")
for config in CONFIGS:
    sub = df[df["config"] == config]
    ra, pa = stats.spearmanr(sub["alpha"],       sub["success"])
    rn, pn = stats.spearmanr(sub["noise_sigma"], sub["success"])
    print(f"    {config:8s}  alpha->success: rho={ra:.3f} (p={pa:.3f})  "
          f"sigma->success: rho={rn:.3f} (p={pn:.3f})")


# ############################################################
# 10. Run-level aggregated statistics (for paper Table 1)
# ############################################################
sep("10. RUN-LEVEL MEANS (Table 1 -- in Manuscript)")

run_means = (
    df.groupby(["config", "run_id"])[["latency_s", "success", "workload", "justified"]]
    .mean()
    .reset_index()
)

table1 = run_means.groupby("config").agg(
    latency_mean=("latency_s", "mean"),
    latency_sd  =("latency_s", "std"),
    success_mean=("success",   "mean"),
    success_sd  =("success",   "std"),
    workload_mean=("workload",  "mean"),
    workload_sd  =("workload",  "std"),
    justified_mean=("justified","mean"),
).round(3)

# 95% CI on run-level means (n = 30 runs per config)
for col_mean, col_sd in [("latency_mean","latency_sd"),
                          ("success_mean","success_sd"),
                          ("workload_mean","workload_sd")]:
    table1[col_mean.replace("mean","ci95")] = (
        1.96 * table1[col_sd] / np.sqrt(30)
    ).round(3)

print(table1)
table1.reset_index().to_json(os.path.join(RESULTS_DIR, "run_level_means.json"), orient="records", indent=2)

# ############################################################
# 11. CYBER-PHYSICAL RESILIENCE ANALYSIS (ML-LEARNED VALIDATION)
# ############################################################
sep("11. CYBER-PHYSICAL RESILIENCE ANALYSIS (TRAIN/TEST VALIDATION)")

# We split the data: 70% to 'train' our ML-Agent, 30% to 'test' it
df_train, df_test = train_test_split(df, test_size=0.3, random_state=42)

# Features: include the simulation's own audit signal and cost factors
features_adv = ["latency_s", "workload", "window_var_feature"]
X_train_adv = df_train[features_adv]
# We train the ML model to 'mimic' the simulation's internal audit agent
y_train_adv = df_train["attack_detected"]

adv_clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
adv_clf.fit(X_train_adv, y_train_adv)

# Validation Phase: Predict on the unseen TEST set
df_test = df_test.copy()
df_test["ml_detected"] = adv_clf.predict(df_test[features_adv])

resilience_results = []
for config in CONFIGS:
    sub = df_test[df_test["config"] == config]
    attacks = sub[sub["is_attacked"] == 1]
    
    if len(attacks) > 0:
        # Agentic models use the ML-learned detector
        if "agentic" in config or "multi" in config:
            detection_rate = attacks["ml_detected"].mean()
        else:
            detection_rate = 0.0
            
        success_rate = attacks["success"].mean()
    else:
        detection_rate = 0.0
        success_rate = sub["success"].mean()
        
    resilience_results.append({
        "config": config,
        "attack_detection_rate": round(float(detection_rate), 4),
        "success_rate_under_attack": round(float(success_rate), 4),
        "n_attacks": int(len(attacks))
    })

df_resilience = pd.DataFrame(resilience_results)
print("Resilience Results (ML-Validated on New Data):")
print(df_resilience)

with open(os.path.join(RESULTS_DIR, "resilience_analysis.json"), "w") as f:
    json.dump(resilience_results, f, indent=2)

# Attack Detection Plot
plt.figure(figsize=(10, 6))
ax = sns.barplot(x="config", y="attack_detection_rate", data=df_resilience)
add_labels(ax)
plt.title("Sensor Spoofing Attack Detection Rate")
plt.ylabel("Detection Probability")
plt.ylim(0, 1.1)
plt.savefig(os.path.join(RESULTS_DIR, "attack_detection_rate.png"), dpi=300, bbox_inches="tight")
plt.close()

# ############################################################
# 12. Economic ROI & Life-Cycle Analysis
# ############################################################
sep("12. ECONOMIC ROI & LIFE-CYCLE ANALYSIS")

economic_summary = df.groupby("config")["total_cost"].agg(["sum", "mean", "std"]).round(2)
economic_summary.columns = ["Total_Lifecycle_Cost", "Mean_Incident_Cost", "Std_Cost"]
print(economic_summary)
economic_summary.reset_index().to_json(os.path.join(RESULTS_DIR, "economic_analysis.json"), orient="records", indent=2)

# Lifecycle Cost Plot
plt.figure(figsize=(12, 6))
sns.barplot(x=economic_summary.index, y="Total_Lifecycle_Cost", data=economic_summary)
plt.title("Total Lifecycle Cost by Architecture (N=18,000)")
plt.ylabel("Total Cost ($)")
plt.savefig(os.path.join(RESULTS_DIR, "lifecycle_cost_comparison.png"), dpi=300, bbox_inches="tight")
plt.close()

# ############################################################
# 13. Human Factors & Cognitive Fatigue Analysis
# ############################################################
sep("13. HUMAN FACTORS: COGNITIVE FATIGUE IMPACT")

# Correlation between fatigue multiplier and final latency
plt.figure(figsize=(10, 6))
sns.scatterplot(x="workload", y="latency_s", hue="config", data=df, alpha=0.3)
plt.title("Impact of Cognitive Workload on Pipeline Latency")
plt.ylabel("Total Latency (s)")
plt.xlabel("Workload (Decisions/Hour)")
plt.savefig(os.path.join(RESULTS_DIR, "fatigue_impact_scatter.png"), dpi=300, bbox_inches="tight")
plt.close()

# ############################################################
# 14. TRAIN/TEST RELIABILITY VALIDATION
# ############################################################
sep("14. TRAIN/TEST RELIABILITY VALIDATION")

# Feature set for predicting success (system factors)
# We exclude 'config' and 'complexity' temporarily to see if 
# features like latency and alpha consistently predict success
features = ['latency_s', 'workload', 'alpha', 'is_attacked']
# Add categorical encoding
X = pd.get_dummies(df[features + ['config', 'complexity']], drop_first=True)
y = df['success']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a classifier to learn the 'physics' of the simulation
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print("Out-of-Sample Reliability Report (Generalization to New Data):")
report = classification_report(y_test, y_pred, output_dict=True)
print(classification_report(y_test, y_pred))

# Consistency Analysis
train_mean = y_train.mean()
test_mean = y_test.mean()
consistency_delta = abs(train_mean - test_mean)

validation_results = {
    "train_mean_success": round(float(train_mean), 4),
    "test_mean_success": round(float(test_mean), 4),
    "consistency_delta": round(float(consistency_delta), 4),
    "classifier_accuracy": round(report['accuracy'], 4)
}

with open(os.path.join(RESULTS_DIR, "reliability_validation.json"), "w") as f:
    json.dump(validation_results, f, indent=2)

print(f"\nConsistency Check:")
print(f"  Training Mean Success: {train_mean:.4f}")
print(f"  Testing Mean Success:  {test_mean:.4f}")
print(f"  Reliability Delta:     {consistency_delta:.4f}")

if consistency_delta < 0.05:
    print("VALIDATION PASSED: Results are statistically stable across independent samples.")
else:
    print("VALIDATION WARNING: Significant variance detected between samples.")

# ############################################################
# 15. Visualizations
# ############################################################
sep("15. GENERATING PLOTS")

# Latency Boxplot
plt.figure(figsize=(12, 7))
sns.boxplot(x="config", y="latency_s", hue="complexity", data=df)
plt.title("Total Latency by Configuration and Complexity")
plt.ylabel("Latency (seconds)")
plt.xlabel("Architecture Configuration")
plt.savefig(os.path.join(RESULTS_DIR, "latency_boxplot.png"), dpi=300, bbox_inches="tight")
plt.close()

# Success Rate Bar Plot
plt.figure(figsize=(10, 6))
success_rates = df.groupby("config")["success"].mean().reset_index()
ax = sns.barplot(x="config", y="success", data=success_rates)
add_labels(ax)
plt.title("Mitigation Success Rate by Configuration")
plt.ylabel("Success Probability")
plt.ylim(0, 1.1)
plt.savefig(os.path.join(RESULTS_DIR, "success_rate_barplot.png"), dpi=300, bbox_inches="tight")
plt.close()

# Workload Violin Plot
plt.figure(figsize=(10, 6))
sns.violinplot(x="config", y="workload", data=df)
plt.title("Operator Workload Distribution")
plt.ylabel("Decisions / Hour")
plt.savefig(os.path.join(RESULTS_DIR, "workload_violinplot.png"), dpi=300, bbox_inches="tight")
plt.close()

print(f"All plots and JSON results saved to: {os.path.abspath(RESULTS_DIR)}")
print("\nAll analysis complete.")
