import numpy as np
import pandas as pd

np.random.seed(42)

N_RUNS = 30
N_INCIDENTS = 120

configs = ["rules", "dt", "agentic"]
complexities = ["low", "medium", "high"]

base_latency = {
    "rules": 85,
    "dt": 55,
    "agentic": 30
}

complexity_penalty = {
    "low": 0,
    "medium": 5,
    "high": 10
}

success_probs = {
    "rules": {"low":0.30,"medium":0.18,"high":0.08},
    "dt": {"low":0.55,"medium":0.44,"high":0.29},
    "agentic": {"low":0.86,"medium":0.80,"high":0.69}
}

workload_mean = {
    "rules": 32,
    "dt": 21,
    "agentic": 9
}

justified_prob = {
    "rules": 0.0,
    "dt": 0.15,
    "agentic": 0.92
}

rows = []

for config in configs:
    for run in range(N_RUNS):
        alpha = np.random.uniform(0.001, 0.01)
        noise_sigma = np.random.uniform(0.001, 0.01)

        for incident in range(N_INCIDENTS):
            complexity = np.random.choice(complexities)

            latency = (
                base_latency[config]
                + complexity_penalty[complexity]
                + 200*noise_sigma
                + np.random.normal(0,5)
            )

            success = np.random.binomial(1, success_probs[config][complexity])
            workload = np.random.normal(workload_mean[config], 2)
            justified = np.random.binomial(1, justified_prob[config])

            rows.append([
                run, config, incident, complexity,
                latency, success, workload, justified,
                alpha, noise_sigma
            ])

df = pd.DataFrame(rows, columns=[
    "run_id","config","incident_id","complexity",
    "latency_s","success","workload",
    "justified","alpha","noise_sigma"
])

df.to_csv("synthetic_agentic_dt_dataset.csv", index=False)
print("Dataset generated successfully.")
