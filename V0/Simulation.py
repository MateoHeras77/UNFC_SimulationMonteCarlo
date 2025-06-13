import numpy as np

# ─── 1. PARAMETERS ───────────────────────────────────────────────────────────────
fan_cost = 32
downtime_cost_per_min = 10
labor_cost_per_hr = 30

# Replacement policy settings
replacement_time = {
    'current': 20,    # minutes when replacing 1 fan
    'proposed': 40    # minutes when replacing all 3 fans
}
fans_replaced = {
    'current': 1,
    'proposed': 3
}

# Distributions
fan_lifetimes = np.array([1000,1100,1200,1300,1400,1500,1600,1700,1800,1900])
fan_probs     = np.array([0.10,0.13,0.25,0.13,0.09,0.12,0.02,0.06,0.05,0.05])

arrival_delays = np.array([20, 30, 45])
delay_probs    = np.array([0.60,0.30,0.10])

num_failures = 45

# ─── 2. SIMULATION FUNCTION ─────────────────────────────────────────────────────
def simulate(policy):
    print(f"\n=== SIMULATING POLICY: {policy.upper()} ===")
    total_cost = 0.0

    for i in range(1, num_failures + 1):
        # --- Sample random variables ---
        life = np.random.choice(fan_lifetimes, p=fan_probs)   # hours until failure
        delay = np.random.choice(arrival_delays, p=delay_probs)  # min until tech arrives

        # --- Policy-specific parameters ---
        rep_time = replacement_time[policy]
        n_fans   = fans_replaced[policy]

        # --- Cost components ---
        rep_cost       = n_fans * fan_cost
        downtime       = delay + rep_time
        dt_cost        = downtime * downtime_cost_per_min
        labor_time_hr  = rep_time / 60.0
        labor_cost     = labor_time_hr * labor_cost_per_hr
        event_cost     = rep_cost + dt_cost + labor_cost

        # --- Debug prints for this event ---
        print(f"\nEvent #{i}")
        print(f"  Sampled fan lifetime   : {life} hrs")
        print(f"  Technician delay       : {delay} min")
        print(f"  Fans replaced          : {n_fans}")
        print(f"  Replacement time       : {rep_time} min")
        print(f"  Replacement cost       : ${rep_cost:.2f}")
        print(f"  Downtime total         : {downtime} min")
        print(f"  Downtime cost          : ${dt_cost:.2f}")
        print(f"  Labour time            : {labor_time_hr:.2f} hr")
        print(f"  Labour cost            : ${labor_cost:.2f}")
        print(f"  → Event total cost     : ${event_cost:.2f}")

        total_cost += event_cost

    print(f"\n→ TOTAL COST ({policy}): ${total_cost:.2f}")
    return total_cost

# ─── 3. MAIN EXECUTION ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    np.random.seed(123)   # for reproducibility

    # Run both policies
    cost_current  = simulate('current')
    cost_proposed = simulate('proposed')

    # Summary
    print("\n" + "="*40)
    print(f"Summary of 45 failures:")
    print(f"  Current policy cost : ${cost_current:.2f}")
    print(f"  Proposed policy cost: ${cost_proposed:.2f}")
    print("="*40)
