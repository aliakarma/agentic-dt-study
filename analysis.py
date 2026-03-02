import pandas as pd
import scipy.stats as stats

df = pd.read_csv("synthetic_agentic_dt_dataset.csv")

summary = df.groupby("config")["latency_s"].agg(["mean","std"])
print(summary)

rules = df[df["config"]=="rules"]["latency_s"]
agentic = df[df["config"]=="agentic"]["latency_s"]

t_stat, p_val = stats.ttest_ind(rules, agentic)
print("T-test:", t_stat, p_val)
