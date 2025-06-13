import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit App: Discrete-Event Simulation for Fan Replacement Policies
st.title("Discrete-Event Monte Carlo Simulator: Fan Replacement Policies")
st.markdown(
    "This app compares two replacement policies by simulating both cost and elapsed time to service a fixed number of failures."
)

# --- Sidebar Inputs ---
st.sidebar.header("Simulation Control")
num_failures = st.sidebar.number_input("Total failures to simulate", min_value=1, value=45)
num_runs = st.sidebar.number_input("Monte Carlo runs", min_value=1, value=1000)
seed = st.sidebar.number_input("Random seed", value=42)

st.sidebar.header("Cost Parameters")
fan_unit_cost = st.sidebar.number_input("Fan unit cost ($)", value=32.0)
downtime_cost_per_min = st.sidebar.number_input("Downtime cost ($ per minute)", value=10.0)
labor_cost_per_hour = st.sidebar.number_input("Labor cost ($ per hour)", value=30.0)

st.sidebar.header("Replacement Times (minutes)")
rep_time_current = st.sidebar.number_input("Replacement time if 1 fan (min)", value=20)
rep_time_proposed = st.sidebar.number_input("Replacement time if 3 fans (min)", value=40)

# --- Distributions ---
st.header("Input Distributions")
fan_lifetimes = [1000,1100,1200,1300,1400,1500,1600,1700,1800,1900]
fan_probs     = [0.10,0.13,0.25,0.13,0.09,0.12,0.02,0.06,0.05,0.05]
delay_times = [20,30,45]
delay_probs = [0.60,0.30,0.10]
st.subheader("Fan Lifetime Distribution")
st.bar_chart(pd.DataFrame({'Probability': fan_probs}, index=fan_lifetimes))
st.subheader("Technician Arrival Delay (minutes)")
st.bar_chart(pd.DataFrame({'Probability': delay_probs}, index=delay_times))

# --- Discrete-Event Simulation Function ---
def simulate_policy_discrete(fans_to_replace, rep_time_min):
    # Initialize three fan lifetimes (in hours)
    remaining = np.random.choice(fan_lifetimes, size=3, p=fan_probs)
    time_elapsed = 0.0  # total operational + downtime in hours
    failures = 0
    total_cost = 0.0

    while failures < num_failures:
        # find next failure: minimum remaining lifetime
        dt_oper = remaining.min()  # hours until next failure
        time_elapsed += dt_oper
        remaining -= dt_oper  # decrement remaining lifetimes
        failed_idx = np.argmin(remaining)

        # sample technician delay
        delay = np.random.choice(delay_times, p=delay_probs)
        downtime_min = delay + rep_time_min
        downtime_hr = downtime_min / 60.0
        time_elapsed += downtime_hr

        # calculate costs
        rep_cost = fans_to_replace * fan_unit_cost
        downtime_cost = downtime_min * downtime_cost_per_min
        labor_cost = (rep_time_min / 60.0) * labor_cost_per_hour
        total_cost += rep_cost + downtime_cost + labor_cost

        # reset lifetimes
        if fans_to_replace == 1:
            remaining[failed_idx] = np.random.choice(fan_lifetimes, p=fan_probs)
        else:
            remaining = np.random.choice(fan_lifetimes, size=3, p=fan_probs)

        failures += 1

    return total_cost, time_elapsed

# --- Run Monte Carlo Simulation ---
st.header("Simulation Execution")
np.random.seed(seed)
results = []
for _ in range(num_runs):
    cost_c, time_c = simulate_policy_discrete(1, rep_time_current)
    cost_p, time_p = simulate_policy_discrete(3, rep_time_proposed)
    results.append((cost_c, time_c, cost_p, time_p))

cols = ['Cost_Current', 'Time_Current_hr', 'Cost_Proposed', 'Time_Proposed_hr']
df = pd.DataFrame(results, columns=cols)
st.subheader("Sample of Simulation Outputs")
st.write(df.head())

# --- Visualizations ---
st.header("Results Visualization")
# Cost histogram\ nfig1, ax1 = plt.subplots()
fig1, ax1 = plt.subplots()
ax1.hist(df['Cost_Current'], bins=30, alpha=0.6, label='Current Policy')
ax1.hist(df['Cost_Proposed'], bins=30, alpha=0.6, label='Proposed Policy')
ax1.set_xlabel('Total Cost ($)')
ax1.set_ylabel('Frequency')
ax1.legend()
st.pyplot(fig1)

# Time histogram\ nfig2, ax2 = plt.subplots()
fig2, ax2 = plt.subplots()
ax2.hist(df['Time_Current_hr'], bins=30, alpha=0.6, label='Current Policy')
ax2.hist(df['Time_Proposed_hr'], bins=30, alpha=0.6, label='Proposed Policy')
ax2.set_xlabel('Elapsed Time (hours)')
ax2.set_ylabel('Frequency')
ax2.legend()
st.pyplot(fig2)

# Cost vs Time scatter
st.subheader("Cost vs. Elapsed Time per Run")
fig3, ax3 = plt.subplots()
ax3.scatter(df['Time_Current_hr'], df['Cost_Current'], alpha=0.5, label='Current Policy', s=10)
ax3.scatter(df['Time_Proposed_hr'], df['Cost_Proposed'], alpha=0.5, label='Proposed Policy', s=10)
ax3.set_xlabel('Elapsed Time (hours)')
ax3.set_ylabel('Total Cost ($)')
ax3.legend()
st.pyplot(fig3)

# --- Summary Statistics ---
st.header("Summary of Results")
st.write(df.describe().T)

# --- Recommendation ---
st.header("Policy Recommendation")
avg_cost_current = df['Cost_Current'].mean()
avg_cost_proposed = df['Cost_Proposed'].mean()
avg_time_current = df['Time_Current_hr'].mean()
avg_time_proposed = df['Time_Proposed_hr'].mean()
st.write(f"Average Cost - Current: ${avg_cost_current:,.2f}")
st.write(f"Average Time - Current: {avg_time_current:,.1f} hr")
st.write(f"Average Cost - Proposed: ${avg_cost_proposed:,.2f}")
st.write(f"Average Time - Proposed: {avg_time_proposed:,.1f} hr")
if (avg_cost_proposed/avg_time_proposed) < (avg_cost_current/avg_time_current):
    st.success("Proposed policy is more cost-effective per operational hour.")
else:
    st.success("Current policy is more cost-effective per operational hour.")
