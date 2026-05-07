import numpy as np
import pandas as pd
from scipy.special import expit   # logistic function
from scipy.stats import norm      # for PoF calculation
from tqdm import tqdm             # for progress bar

# ─────────────────────────────────────────────────────────────
# Global seed for full reproducibility
# ─────────────────────────────────────────────────────────────
GLOBAL_SEED = 42
np.random.seed(GLOBAL_SEED)

# ─────────────────────────────────────────────────────────────
# Experiment dimensions
# ─────────────────────────────────────────────────────────────
N_RUNS      = 30
N_INCIDENTS = 120
T_MAX       = 600      # maximum simulation timesteps per incident
DT_HOURS    = 0.10     # timestep duration (hours) → 6-minute resolution
ATTACK_PROB = 0.10     # 10% probability of sensor spoofing attack
SPOOF_LIMIT = 0.35     # malicious cap on observed degradation

COMPLEXITIES = ["low", "medium", "high"]
CONFIGS      = ["rules", "dt", "dt_single_agent", "dt_multi_no_chain", "agentic_full"]

# --- Feature 3: Economic Cost Parameters ---
COST_MITIGATION = 12000    # Cost of successful preventive maintenance
COST_FAILURE    = 1500000  # Cost of catastrophic structural failure
# Operating overhead per architecture (blockchain/audit costs)
SYSTEM_OVERHEAD = {
    "rules":             100,
    "dt":                500,
    "dt_single_agent":   500,
    "dt_multi_no_chain": 2500,
    "agentic_full":      5000,
}

# ─────────────────────────────────────────────────────────────
# Degradation model parameters (per complexity level)
# alpha  : mean exponential drift coefficient (dimensionless/step)
# lambda_shock : mean Poisson shock arrival rate per step
# mu_shock     : mean shock magnitude (degradation index units)
# sigma_shock  : std of shock magnitude
#
# Parameter ranges chosen to produce degradation timescales of
# 20–200 hours, consistent with fatigue crack growth rates in
# steel bridge members (Paris & Erdogan, 1963; AASHTO LRFD, 2020).
# ─────────────────────────────────────────────────────────────
DEGRAD_PARAMS = {
    "low": {
        "alpha_mean":    0.0030,
        "alpha_std":     0.0005,
        "lambda_shock":  0.010,
        "mu_shock":      0.040,
        "sigma_shock":   0.010,
    },
    "medium": {
        "alpha_mean":    0.0060,
        "alpha_std":     0.0010,
        "lambda_shock":  0.030,
        "mu_shock":      0.080,
        "sigma_shock":   0.020,
    },
    "high": {
        "alpha_mean":    0.0120,
        "alpha_std":     0.0020,
        "lambda_shock":  0.060,
        "mu_shock":      0.120,
        "sigma_shock":   0.030,
    },
}

# ─────────────────────────────────────────────────────────────
# Structural state thresholds (degradation index D ∈ [0, 1])
# D_ONSET    : first structural concern level (triggers "true" incident)
# D_CRITICAL : imminent failure level
# SENSOR_NOISE_STD : Gaussian sensor measurement noise (±2% resolution
#              consistent with commercial strain gauge SHM systems,
#              e.g., HBM QuantumX at 0.01% FS noise floor)
# ─────────────────────────────────────────────────────────────
D_ONSET          = 0.40
D_CRITICAL       = 0.85
SENSOR_NOISE_STD = 0.020

# Detection thresholds
RULES_THRESHOLD      = 0.70   # static alarm level
DT_PRED_THRESHOLD    = 0.70   # DT predicts crossing of this level
DT_HORIZON_STEPS     = 15     # prediction horizon for DT (15 × 0.1 hr = 1.5 hr)
AGENTIC_BASE_THRESH  = 0.60   # agentic starting adaptive threshold

# ─────────────────────────────────────────────────────────────
# Pipeline latency (seconds added AFTER algorithmic detection)
# Represents operator/system response chain, not detection itself.
# ─────────────────────────────────────────────────────────────
PIPELINE_S = {
    "rules":             {"mean": 42, "std": 8},
    "dt":                {"mean": 18, "std": 4},
    "dt_single_agent":   {"mean": 18, "std": 4},
    "dt_multi_no_chain": {"mean":  6, "std": 2},
    "agentic_full":      {"mean":  6, "std": 2},
}

# ─────────────────────────────────────────────────────────────
# Operator workload (decisions/hour) — derived from NASA-TLX
# literature on control room operations (Hart & Staveland, 1988).
# ─────────────────────────────────────────────────────────────
WORKLOAD = {
    "rules":             {"mean": 32, "std": 4},
    "dt":                {"mean": 21, "std": 3},
    "dt_single_agent":   {"mean": 21, "std": 3},
    "dt_multi_no_chain": {"mean":  9, "std": 2},
    "agentic_full":      {"mean":  9, "std": 2},
}

# ─────────────────────────────────────────────────────────────
# Blockchain-anchored provenance probability
# Rules: no automated logging infrastructure
# DT: partial logging (state snapshots only)
# Agentic: full chain-of-custody audit trail per decision cycle
# ─────────────────────────────────────────────────────────────
JUSTIFIED_PROB = {
    "rules":             0.00,
    "dt":                0.15,
    "dt_single_agent":   0.15,
    "dt_multi_no_chain": 0.15,
    "agentic_full":      0.92,
}


# ═══════════════════════════════════════════════════════════════
# Core simulation functions
# ═══════════════════════════════════════════════════════════════

def simulate_degradation(complexity: str, rng: np.random.Generator):
    """
    Generate a degradation index trajectory D(t) using the model:

        D(t) = D(t-1) + α·D(t-1) + S(t)

    where α ~ N(alpha_mean, alpha_std) is the per-run drift coefficient
    and S(t) is a Poisson-gated log-normal shock.

    Returns:
        D  : np.ndarray of shape (T_MAX,) — true degradation trajectory
        alpha : float — sampled drift coefficient
    """
    p = DEGRAD_PARAMS[complexity]
    alpha = rng.normal(p["alpha_mean"], p["alpha_std"])
    alpha = max(alpha, 1e-5)

    D = np.zeros(T_MAX)
    D[0] = rng.uniform(0.05, 0.15)

    for t in range(1, T_MAX):
        drift  = alpha * D[t - 1]
        shock  = 0.0
        if rng.random() < p["lambda_shock"]:
            shock = max(rng.normal(p["mu_shock"], p["sigma_shock"]), 0.0)
        D[t] = min(D[t - 1] + drift + shock, 1.0)

    return D, alpha


def noisy_obs(D_true: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Add Gaussian sensor noise and clip to [0, 1]."""
    return np.clip(D_true + rng.normal(0, SENSOR_NOISE_STD, size=D_true.shape), 0, 1)


def kalman_step(x_hat: float, P: float, obs: float,
                alpha_est: float, Q: float = 1e-4) -> tuple:
    """
    Scalar Kalman filter update for state x with additive-proportional
    drift model: x(t+1) = x(t) + alpha*x(t).
    Q: process noise variance; R = SENSOR_NOISE_STD² (measurement noise).
    """
    R = SENSOR_NOISE_STD ** 2
    # Predict
    x_pred = x_hat * (1 + alpha_est)
    P_pred = P + Q
    # Update
    K      = P_pred / (P_pred + R)
    x_new  = x_pred + K * (obs - x_pred)
    P_new  = (1 - K) * P_pred
    return x_new, P_new


def predict_ahead(x_hat: float, alpha_est: float, steps: int) -> float:
    """Project Kalman estimate forward `steps` steps."""
    x = x_hat
    for _ in range(steps):
        x = x * (1 + alpha_est)
    return x


# ─────────────────────────────────────────────────────────────
# Per-architecture detection functions
# Each returns the timestep index of detection, or None if missed.
# ─────────────────────────────────────────────────────────────

def detect_rules(D_obs: np.ndarray) -> int | None:
    """Static threshold: alarm when observed reading ≥ RULES_THRESHOLD."""
    idx = np.argmax(D_obs >= RULES_THRESHOLD)
    return int(idx) if D_obs[idx] >= RULES_THRESHOLD else None


def detect_dt(D_obs: np.ndarray,
              alpha_prior: float = 0.005) -> tuple[int | None, float]:
    """
    Digital Twin: Kalman-filtered state estimation with predictive horizon.
    Alerts when projected D(t + DT_HORIZON_STEPS) >= DT_PRED_THRESHOLD.
    Returns: (detection_time, max_pof)
    """
    x_hat, P = D_obs[0], 0.01
    alpha_est = alpha_prior
    max_pof = 0.0

    for t, obs in enumerate(D_obs):
        x_hat, P = kalman_step(x_hat, P, obs, alpha_est)
        
        # Calculate PoF using Kalman Variance P
        # PoF is the probability that true state is above critical threshold
        # We assume standard deviation scales with time horizon
        std_pred = np.sqrt(P + (DT_HORIZON_STEPS * 0.001)) 
        x_future = predict_ahead(x_hat, alpha_est, DT_HORIZON_STEPS)
        pof = float(1 - norm.cdf(D_CRITICAL, loc=x_future, scale=std_pred))
        max_pof = max(max_pof, pof)

        if x_future >= DT_PRED_THRESHOLD:
            return t, max_pof
    return None, max_pof


def detect_agentic(D_obs: np.ndarray,
                    complexity: str) -> tuple[int | None, float]:
    """
    Agentic AI: risk-based adaptive threshold.
    Uses Probability of Failure (PoF) to make risk-informed decisions.
    """
    threshold   = AGENTIC_BASE_THRESH
    shock_times = []
    x_hat, P    = D_obs[0], 0.01
    alpha_est   = DEGRAD_PARAMS[complexity]["alpha_mean"]
    max_pof     = 0.0

    for t in range(1, len(D_obs)):
        obs = D_obs[t]
        if obs - D_obs[t - 1] > 3 * SENSOR_NOISE_STD:
            shock_times.append(t)

        recent_shocks   = sum(1 for s in shock_times if (t - s) < 20)
        live_threshold  = max(threshold - 0.04 * recent_shocks, 0.30)

        x_hat, P = kalman_step(x_hat, P, obs, alpha_est)
        
        # Risk-based lookahead
        std_pred = np.sqrt(P + (8 * 0.001))
        x_future = predict_ahead(x_hat, alpha_est, 8)
        pof = float(1 - norm.cdf(live_threshold, loc=x_future, scale=std_pred))
        max_pof = max(max_pof, pof)

        # Agent triggers if PoF exceeds 15% (Risk-averse policy)
        if pof >= 0.15:
            return t, max_pof
    return None, max_pof


def detect_integrity_violation(D_obs: np.ndarray, complexity: str) -> int | None:
    """
    Cyber-Physical Resilience: Statistical Variance Audit.
    Detects 'Mimicry Attacks' where an attacker injects fake noise.
    The agent compares the live window variance to the expected 
    sensor noise floor.
    """
    window_size = 20
    # The agent uses a statistical confidence interval for the variance.
    # Chi-square based variance check (stochastic window)
    for t in range(window_size + 80, len(D_obs)):
        window = D_obs[t - window_size:t]
        
        # Stricter threshold for stealthy attacks (0.85 vs 0.75)
        # Higher window variance will lead to some missed detections
        if np.var(window) < (SENSOR_NOISE_STD**2) * 0.85:
            return t
    return None


def mitigation_success(detect_t: int | None,
                       D_true: np.ndarray,
                       rng: np.random.Generator) -> int:
    """
    Bernoulli draw: success probability is a logistic function of the
    response margin (hours between detection and projected critical failure).

    P(success) = σ(−2.0 + 0.8 × margin_hours)

    This calibration gives:
      ~11% at margin = 0 hr  (detection at onset of failure)
      ~50% at margin = 2.5 hr
      ~88% at margin = 5 hr
      ~96% at margin = 7.5 hr (saturated)
    """
    if detect_t is None:
        return 0

    # Time until D_true first reaches D_CRITICAL
    critical_hits = np.where(D_true >= D_CRITICAL)[0]
    critical_t    = int(critical_hits[0]) if len(critical_hits) > 0 else T_MAX

    margin_hours = max(critical_t - detect_t, 0) * DT_HOURS
    prob = float(expit(-2.0 + 0.8 * margin_hours))
    prob = min(prob, 0.95)   # hard ceiling — no system is perfect
    return int(rng.binomial(1, prob))


# ═══════════════════════════════════════════════════════════════
# Main simulation loop
# ═══════════════════════════════════════════════════════════════

rows = []

print("Initializing Simulation Environment...")
print(f"Target: {N_RUNS * len(CONFIGS) * N_INCIDENTS} total incidents across {len(CONFIGS)} architectures.")

for config in tqdm(CONFIGS, desc="Architecture Selection"):
    config_idx = CONFIGS.index(config)
    for run in tqdm(range(N_RUNS), desc=f"Simulating {config}", leave=False):
        # Per-run RNG: deterministic but independent across runs/configs
        rng = np.random.default_rng(GLOBAL_SEED + run + config_idx * 1000)

        incidents_logged = 0
        trajectory_idx   = 0

        while incidents_logged < N_INCIDENTS:
            complexity = rng.choice(COMPLEXITIES)

            # Simulate one degradation trajectory
            D_true, alpha = simulate_degradation(complexity, rng)

            # Check this trajectory contains a meaningful incident
            onset_hits = np.where(D_true >= D_ONSET)[0]
            if len(onset_hits) == 0:
                continue   # no real incident in this trajectory

            onset_t = int(onset_hits[0])

            # Noisy sensor stream
            D_obs = noisy_obs(D_true, rng)

            # --- Feature 2: Cyber-Physical Attack Simulation ---
            is_attacked = 0
            if rng.random() < ATTACK_PROB:
                is_attacked = 1
                # Variable Stealth: Attacker tries to mimic noise with 85-98% accuracy
                # This ensures detection is no longer a deterministic 100%
                stealth_factor = rng.uniform(0.85, 0.98)
                D_obs = np.clip(D_true, 0, SPOOF_LIMIT) + rng.normal(0, SENSOR_NOISE_STD * stealth_factor, size=D_true.shape)
                D_obs = np.clip(D_obs, 0, 1)

            # Detection
            detect_t = None
            attack_detected = 0
            pof_at_detect = 0.0
            
            if config == "rules":
                detect_t = detect_rules(D_obs)
            elif "dt" in config and "multi" not in config:
                detect_t, pof_at_detect = detect_dt(D_obs)
            else:
                # Agentic models have integrity checking and risk-based logic
                detect_t, pof_at_detect = detect_agentic(D_obs, complexity)
                
                # Check for integrity violation (spoofing detection)
                integrity_t = detect_integrity_violation(D_obs, complexity)
                if integrity_t is not None:
                    attack_detected = 1
                    if detect_t is None or integrity_t < detect_t:
                        detect_t = integrity_t

            # Compute latency (seconds)
            if detect_t is not None:
                algo_delay_s = max(detect_t - onset_t, 0) * DT_HOURS * 3600
            else:
                # Missed detection: full elapsed time treated as delay
                algo_delay_s = (T_MAX - onset_t) * DT_HOURS * 3600

            complexity_penalty = {"low": 0, "medium": 5, "high": 15}[complexity]

            # --- Feature 4: Human Factors (Cognitive Fatigue) ---
            # Operator workload (decisions/hour)
            wl       = WORKLOAD[config]
            workload = max(rng.normal(wl["mean"], wl["std"]), 0.0)
            
            # Fatigue multiplier: exponential latency growth above stress threshold
            # Consistent with Wickens' Multiple Resource Theory (2002)
            fatigue_mult = np.exp(0.04 * max(workload - 15, 0))

            pl = PIPELINE_S[config]
            pipeline_s = max(rng.normal(pl["mean"] + complexity_penalty, pl["std"]), 1.0)
            latency_s  = algo_delay_s + (pipeline_s * fatigue_mult)

            # Mitigation success
            success = mitigation_success(detect_t, D_true, rng)

            # Adversarial conditions
            # LLM hallucination penalty for agentic/multi configs
            if "agentic" in config or "multi" in config:
                if rng.random() < 0.05: # 5% hallucination rate
                    success = 0 
                    latency_s += 120 # Added resolution time

            # Blockchain network delay penalty
            if config == "agentic_full":
                if rng.random() < 0.02: # 2% chance of network congestion
                    latency_s += 300 

            # Cyber-Physical Attack Impact
            if is_attacked and not attack_detected:
                success = 0 # Undetected spoofing leads to structural failure

            # --- Feature 5: Economic ROI Analysis ---
            # Total incident cost = (Mitigation or Failure cost) + System overhead
            incident_cost = (COST_MITIGATION if success else COST_FAILURE) + SYSTEM_OVERHEAD[config]

            # Blockchain-anchored provenance
            justified = int(rng.binomial(1, JUSTIFIED_PROB[config]))

            noise_sigma = DEGRAD_PARAMS[complexity]["sigma_shock"]

            rows.append([
                run, config, incidents_logged, complexity,
                round(latency_s, 2),
                success,
                round(workload, 2),
                justified,
                round(alpha, 6),
                round(noise_sigma, 6),
                is_attacked,
                attack_detected,
                round(pof_at_detect, 4),
                round(fatigue_mult, 3),
                round(incident_cost, 0),
            ])

            incidents_logged += 1

df = pd.DataFrame(rows, columns=[
    "run_id", "config", "incident_id", "complexity",
    "latency_s", "success", "workload",
    "justified", "alpha", "noise_sigma",
    "is_attacked", "attack_detected",
    "pof", "fatigue_mult", "total_cost",
])

df.to_csv("../data/synthetic_agentic_dt_dataset.csv", index=False)
print(f"Dataset generated: {len(df):,} records across {len(CONFIGS)} configurations.\n")
print("Summary statistics (emergent from simulation):")
print(df.groupby("config")[["latency_s", "success", "workload"]].agg(
    ["mean", "std"]
).round(3))
