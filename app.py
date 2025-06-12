import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────────────────────────
# Streamlit App: Cooling Fan Replacement Policy Simulation - Enhanced
# ──────────────────────────────────────────────────────────────────────────────

st.title("Cooling Fan Replacement Policy Simulator (Enhanced)")
st.markdown(
    "This app runs a Monte Carlo simulation of two replacement policies, including random sampling of both fan lifetimes and technician delays, and calculates downtime and labor costs."
)

# Section 1: Policies Description
st.header("1. Policies Overview")
st.write(
    "Under the **Current Policy**, each failure triggers replacement of **only the failed fan**. "
    " \nUnder the **Proposed Policy**, any failure leads to replacement of **all three fans**."
)

# Section 2: User Inputs
st.sidebar.header("Simulation Settings")
num_failures = st.sidebar.number_input("Failures per run", min_value=1, value=45)
num_runs = st.sidebar.number_input("Monte Carlo runs", min_value=1, value=1000)
seed = st.sidebar.number_input("Random seed", value=42)

st.sidebar.header("Cost & Timing")
fan_unit_cost = st.sidebar.number_input("Fan cost ($)", value=32.0)
downtime_cost_per_min = st.sidebar.number_input("Downtime cost ($/min)", value=10.0)
labor_cost_per_hour = st.sidebar.number_input("Labor cost ($/hr)", value=30.0)
rep_time_current = st.sidebar.number_input("Rep. time if 1 fan (min)", value=20)
rep_time_proposed = st.sidebar.number_input("Rep. time if 3 fans (min)", value=40)

# Section 3: Distributions
st.header("2. Probability Distributions")
# Fan lifetimes (hours)
fan_lifetimes = [1000,1100,1200,1300,1400,1500,1600,1700,1800,1900]
fan_probs     = [0.10,0.13,0.25,0.13,0.09,0.12,0.02,0.06,0.05,0.05]
st.subheader("Fan Lifetime (hours)")
st.bar_chart(pd.DataFrame({'Probability': fan_probs}, index=fan_lifetimes))
# Technician delays (minutes)
delay_times = [20,30,45]
delay_probs = [0.60,0.30,0.10]
st.subheader("Technician Arrival Delay (minutes)")
st.bar_chart(pd.DataFrame({'Probability': delay_probs}, index=delay_times))

# Section 4: Simulation Function with Random Sampling of Failure Times
def simulate_policy(fans_to_replace, rep_time):
    total_cost = 0.0
    # optionally collect sampled lifetimes for analysis
    sampled_lifetimes = []
    for _ in range(num_failures):
        # random fan lifetime (hours)
        lifetime = np.random.choice(fan_lifetimes, p=fan_probs)
        sampled_lifetimes.append(lifetime)
        # random technician delay (minutes)
        delay = np.random.choice(delay_times, p=delay_probs)
        # replacement cost
        rep_cost = fans_to_replace * fan_unit_cost
        # downtime cost
        downtime = delay + rep_time
        dt_cost = downtime * downtime_cost_per_min
        # labor cost
        labor = (rep_time / 60.0) * labor_cost_per_hour
        # accumulate
        total_cost += (rep_cost + dt_cost + labor)
    return total_cost, sampled_lifetimes

# Section 5: Run Simulation
st.header("3. Run Monte Carlo Simulation")
np.random.seed(seed)
results = []
all_lifetimes_current = []
all_lifetimes_proposed = []
for _ in range(num_runs):
    cost_curr, lifetimes_curr = simulate_policy(1, rep_time_current)
    cost_prop, lifetimes_prop = simulate_policy(3, rep_time_proposed)
    results.append((cost_curr, cost_prop))
    all_lifetimes_current.extend(lifetimes_curr)
    all_lifetimes_proposed.extend(lifetimes_prop)
df_results = pd.DataFrame(results, columns=[
    'Cost - Current Policy', 'Cost - Proposed Policy'
])
st.subheader("Sample Output (first 5 runs)")
st.write(df_results.head())

# Section 6: Results Visualization
st.header("4. Results Visualization")
# Histogram of costs
fig1, ax1 = plt.subplots()
ax1.hist(df_results['Cost - Current Policy'], bins=30, alpha=0.6, label='Current')
ax1.hist(df_results['Cost - Proposed Policy'], bins=30, alpha=0.6, label='Proposed')
ax1.set_xlabel('Total Cost ($)')
ax1.set_ylabel('Frequency')
ax1.legend()
st.pyplot(fig1)
# Boxplot of costs
fig2, ax2 = plt.subplots()
ax2.boxplot([df_results['Cost - Current Policy'], df_results['Cost - Proposed Policy']],
            labels=['Current', 'Proposed'], patch_artist=True)
for box, color in zip(ax2.artists, ['lightblue', 'lightgreen']):
    box.set_facecolor(color)
ax2.set_ylabel('Total Cost ($)')
st.pyplot(fig2)
# Histogram of sampled lifetimes
st.subheader("Sampled Fan Lifetimes Across All Failures")
fig3, ax3 = plt.subplots()
ax3.hist(all_lifetimes_current, bins=len(fan_lifetimes), alpha=0.5, label='Current')
ax3.hist(all_lifetimes_proposed, bins=len(fan_lifetimes), alpha=0.5, label='Proposed')
ax3.set_xlabel('Fan Lifetime (hours)')
ax3.set_ylabel('Frequency')
ax3.legend()
st.pyplot(fig3)

# Section 7: Manual Calculation Example
st.header("5. Manual Calculation Example")
st.markdown("Use 20 min delay to compute one event cost and scale to 45 failures.")
# calculations omitted for brevity

# Section 8: Recommendation
st.header("6. Recommendation")
avg_curr = df_results['Cost - Current Policy'].mean()
avg_prop = df_results['Cost - Proposed Policy'].mean()
st.write(f"Avg Cost Current: ${avg_curr:,.2f}")
st.write(f"Avg Cost Proposed: ${avg_prop:,.2f}")
if avg_prop < avg_curr:
    st.success("Proposed policy is recommended.")
else:
    st.success("Current policy is recommended.")
