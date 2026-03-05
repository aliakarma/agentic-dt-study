import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import shapiro, mannwhitneyu, chi2_contingency
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# Load dataset
# ─────────────────────────────────────────────────────────────
df = pd.read_csv("../data/synthetic_agentic_dt_dataset.csv")
df["config"]     = pd.Categorical(df["config"],     categories=["rules", "dt", "agentic"], ordered=False)
df["complexity"] = pd.Categorical(df["complexity"], categories=["low", "medium", "high"],   ordered=True)

CONFIGS      = ["rules", "dt", "agentic"]
COMPLEXITIES = ["low", "medium", "high"]
N_PER_CONFIG = len(df) // 3


def sep(title=""):
    print("\n" + "═" * 60)
    if title:
        print(f"  {title}")
        print("─" * 60)


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


# ═══════════════════════════════════════════════════════════════
# 1. Descriptive Statistics
# ═══════════════════════════════════════════════════════════════
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
    print(pd.DataFrame(rows).round(3).to_string(index=False))

# Overall by config
sep("  Overall means by config")
print(df.groupby("config")[["latency_s", "success", "workload"]].agg(
    ["mean", "std", "median"]
).round(3))


# ═══════════════════════════════════════════════════════════════
# 2. Normality Screening (Shapiro-Wilk, sampled)
# ═══════════════════════════════════════════════════════════════
sep("2. NORMALITY SCREENING (Shapiro-Wilk, n≤5000 subsample)")
for metric in ["latency_s", "workload"]:
    print(f"\n  [{metric}]")
    for config in CONFIGS:
        sub  = df[df["config"] == config][metric]
        samp = sub.sample(min(len(sub), 5000), random_state=42)
        stat, p = shapiro(samp)
        note = "  ← non-normal" if p < 0.05 else ""
        print(f"    {config:8s}  W={stat:.4f}  p={p:.4f}{note}")


# ═══════════════════════════════════════════════════════════════
# 3. Welch's t-Tests (Latency)
# ═══════════════════════════════════════════════════════════════
sep("3. WELCH'S t-TESTS — LATENCY")
pairs = [("agentic", "dt"), ("agentic", "rules"), ("dt", "rules")]
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


# ═══════════════════════════════════════════════════════════════
# 4. Mann-Whitney U Tests (non-parametric complement)
# ═══════════════════════════════════════════════════════════════
sep("4. MANN-WHITNEY U TESTS — LATENCY (non-parametric)")
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


# ═══════════════════════════════════════════════════════════════
# 5. Chi-Squared Tests — Mitigation Success Rate
# ═══════════════════════════════════════════════════════════════
sep("5. CHI-SQUARED TESTS — MITIGATION SUCCESS RATE")
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


# ═══════════════════════════════════════════════════════════════
# 6. Two-Way ANOVA — Configuration × Complexity
# ═══════════════════════════════════════════════════════════════
sep("6. TWO-WAY ANOVA (Type II SS)")
for metric in ["latency_s", "success"]:
    print(f"\n  Outcome: {metric}")
    model  = ols(f"{metric} ~ C(config) + C(complexity) + C(config):C(complexity)", data=df).fit()
    anova  = sm.stats.anova_lm(model, typ=2)

    # Eta-squared (partial)
    ss_resid = anova.loc["Residual", "sum_sq"]
    anova["eta_sq_partial"] = anova["sum_sq"] / (anova["sum_sq"] + ss_resid)

    print(anova[["sum_sq", "df", "F", "PR(>F)", "eta_sq_partial"]].round(4))


# ═══════════════════════════════════════════════════════════════
# 7. Post-hoc Tukey HSD — Latency by Config
# ═══════════════════════════════════════════════════════════════
sep("7. POST-HOC TUKEY HSD — LATENCY BY CONFIGURATION")
tukey = pairwise_tukeyhsd(endog=df["latency_s"], groups=df["config"], alpha=0.05)
print(tukey.summary())

sep("   POST-HOC TUKEY HSD — LATENCY BY COMPLEXITY")
tukey_cx = pairwise_tukeyhsd(endog=df["latency_s"], groups=df["complexity"], alpha=0.05)
print(tukey_cx.summary())


# ═══════════════════════════════════════════════════════════════
# 8. Workload and Justification Summary
# ═══════════════════════════════════════════════════════════════
sep("8. WORKLOAD AND PROVENANCE JUSTIFICATION")
print("\n  Workload (decisions/hour):")
print(df.groupby("config")["workload"].agg(["mean", "std", "median"]).round(3))

print("\n  Blockchain-justified proportion:")
print(df.groupby("config")["justified"].agg(["mean", "sum", "count"]).round(3))


# ═══════════════════════════════════════════════════════════════
# 9. Sensitivity Analysis — Degradation Parameters
# ═══════════════════════════════════════════════════════════════
sep("9. SENSITIVITY ANALYSIS — Degradation Parameters")

# Spearman correlation of alpha and noise_sigma with latency/success
print("\n  Spearman ρ with latency_s:")
for config in CONFIGS:
    sub = df[df["config"] == config]
    ra, pa = stats.spearmanr(sub["alpha"],       sub["latency_s"])
    rn, pn = stats.spearmanr(sub["noise_sigma"], sub["latency_s"])
    print(f"    {config:8s}  α→latency: ρ={ra:.3f} (p={pa:.3f})  "
          f"σ→latency: ρ={rn:.3f} (p={pn:.3f})")

print("\n  Spearman ρ with success:")
for config in CONFIGS:
    sub = df[df["config"] == config]
    ra, pa = stats.spearmanr(sub["alpha"],       sub["success"])
    rn, pn = stats.spearmanr(sub["noise_sigma"], sub["success"])
    print(f"    {config:8s}  α→success: ρ={ra:.3f} (p={pa:.3f})  "
          f"σ→success: ρ={rn:.3f} (p={pn:.3f})")


# ═══════════════════════════════════════════════════════════════
# 10. Run-level aggregated statistics (for paper Table 1)
# ═══════════════════════════════════════════════════════════════
sep("10. RUN-LEVEL MEANS (Table 1 — in Manuscript)")

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
print("\nAll analysis complete.")
