# streamlit_fan_replacement_policies_updated.py

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, ttest_rel

# -----------------------------
# 1. Page & Sidebar Inputs
# -----------------------------
st.set_page_config(layout="wide")
st.title("Cooling Fan Replacement Policy Simulation (Updated Distributions)")

# Sidebar: simulation controls
seed     = st.sidebar.number_input("Random seed", value=42, step=1)
n_trials = st.sidebar.number_input("Monte Carlo trials", min_value=100, value=1000, step=100)
n_fail   = st.sidebar.number_input("Failures per trial", min_value=1, value=45, step=1)
st.sidebar.markdown("---")

# Sidebar: cost parameters
FAN_COST      = st.sidebar.number_input("Fan cost ($)", value=32, step=1)
DOWNTIME_RATE = st.sidebar.number_input("Downtime cost ($/min)", value=10, step=1)
LABOR_RATE    = st.sidebar.number_input("Labor rate ($/hr)", value=30, step=1)
st.sidebar.markdown("---")

# Sidebar: replacement times
rt1 = st.sidebar.number_input("Replacement time for 1 fan (min)", value=20, step=1)
rt2 = st.sidebar.number_input("Replacement time for 2 fans (min)", value=30, step=1)
rt3 = st.sidebar.number_input("Replacement time for 3 fans (min)", value=40, step=1)
REPLACEMENT_TIME = {1: rt1, 2: rt2, 3: rt3}

# -----------------------------
# 2. Updated Distributions
# -----------------------------
# Table 1: operational life distribution
LIFETIME_DISTS = pd.DataFrame({
    "Lifetime (hrs)": [1000, 1100, 1200, 1300, 1400, 
                       1500, 1600, 1700, 1800, 1900],
    "Probability":    [0.10,  0.13,  0.25,  0.13,  0.09,
                       0.12,  0.02,  0.06,  0.05,  0.05]
})

# Table 2: technician arrival time distribution
DELAY_DISTS = pd.DataFrame({
    "Delay (min)": [20, 30, 45],
    "Probability": [0.60, 0.30, 0.10]
})

# Sidebar note
st.sidebar.markdown("---")
st.sidebar.write("Fan‐life and delay distributions updated per user request.")

# Seed RNG
np.random.seed(int(seed))

# Show distributions and bar charts
st.subheader("Input Distributions")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Fan Lifetime Distribution**")
    st.table(LIFETIME_DISTS)
    fig_life, ax_life = plt.subplots()
    ax_life.bar(LIFETIME_DISTS["Lifetime (hrs)"], LIFETIME_DISTS["Probability"])
    ax_life.set_xlabel("Lifetime (hrs)")
    ax_life.set_ylabel("Probability")
    ax_life.set_title("Fan Lifetime Distribution")
    st.pyplot(fig_life)

with col2:
    st.markdown("**Technician Delay Distribution**")
    st.table(DELAY_DISTS)
    fig_delay, ax_delay = plt.subplots()
    ax_delay.bar(DELAY_DISTS["Delay (min)"], DELAY_DISTS["Probability"])
    ax_delay.set_xlabel("Delay (min)")
    ax_delay.set_ylabel("Probability")
    ax_delay.set_title("Technician Delay Distribution")
    st.pyplot(fig_delay)

# -----------------------------
# 3. Cost Calculation Helper
# -----------------------------
def calculate_costs(downtime_min, num_fans):
    labor_cost    = (downtime_min / 60) * LABOR_RATE
    fan_cost      = num_fans * FAN_COST
    downtime_cost = downtime_min * DOWNTIME_RATE
    total_cost    = labor_cost + fan_cost + downtime_cost
    return total_cost, labor_cost, fan_cost, downtime_cost

# -----------------------------
# 4. Tabbed Layout
# -----------------------------
tab1, tab2 = st.tabs([
    "Total Cost per 45 Failures",
    "Cost per Operational Hour (CRN)"
])

# -----------------------------
# Tab 1: Total cost over fixed # failures
# -----------------------------
with tab1:
    st.header("Policy Comparison: Total Cost over 45 Failures")

    def run_total_policy(replace_count):
        costs = []
        for _ in range(int(n_trials)):
            cum_cost = 0.0
            for _ in range(int(n_fail)):
                # draw one lifetime (we're not tracking aging here)
                _       = np.random.choice(
                              LIFETIME_DISTS["Lifetime (hrs)"],
                              p=LIFETIME_DISTS["Probability"])
                delay   = np.random.choice(
                              DELAY_DISTS["Delay (min)"],
                              p=DELAY_DISTS["Probability"])
                downtime = delay + REPLACEMENT_TIME[replace_count]
                c, lc, fc, dc = calculate_costs(downtime, replace_count)
                cum_cost += c
            costs.append(cum_cost)
        return np.array(costs)

    curr_total = run_total_policy(1)
    prop_total = run_total_policy(3)

    # Averages & bar chart
    avg_table = pd.DataFrame({
        "Policy": ["Current", "Proposed"],
        "Avg Total Cost ($)": [curr_total.mean(), prop_total.mean()]
    }).set_index("Policy")
    st.write("**Average Total Cost**")
    st.table(avg_table)

    fig_avg, ax_avg = plt.subplots()
    ax_avg.bar(avg_table.index, avg_table["Avg Total Cost ($)"])
    ax_avg.set_ylabel("Average Cost ($)")
    ax_avg.set_title("Average Total Cost by Policy")
    st.pyplot(fig_avg)

    # Histograms
    fig_h, (ax1h, ax2h) = plt.subplots(1,2, figsize=(8,3))
    ax1h.hist(curr_total, bins=30)
    ax1h.set_title("Current Policy Costs")
    ax1h.set_xlabel("Total Cost ($)")
    ax1h.set_ylabel("Frequency")
    ax2h.hist(prop_total, bins=30)
    ax2h.set_title("Proposed Policy Costs")
    ax2h.set_xlabel("Total Cost ($)")
    ax2h.set_ylabel("Frequency")
    st.pyplot(fig_h)

    # t-test
    t_stat, p_val = ttest_ind(curr_total, prop_total, equal_var=False)
    st.write(f"Two-sample t-test (unequal var): t = {t_stat:.3f}, p = {p_val:.3e}")
    if p_val < 0.05:
        better = "Current" if curr_total.mean() < prop_total.mean() else "Proposed"
        st.success(f"{better} Policy is significantly lower total cost (α=0.05).")
    else:
        st.info("No significant difference in total cost (α=0.05).")

# -----------------------------
# Tab 2: Continuous aging & cost/hour
# -----------------------------
with tab2:
    st.header("Policy Comparison: Cost per Hour (Continuous Aging + CRN)")

    rs = np.random.RandomState(int(seed))

    def simulate_rate_trial(replace_all):
        lives = rs.choice(
                    LIFETIME_DISTS["Lifetime (hrs)"], size=3,
                    p=LIFETIME_DISTS["Probability"]).astype(float)
        total_hours = 0.0
        total_cost  = 0.0
        for _ in range(int(n_fail)):
            t_fail = lives.min()
            total_hours += t_fail
            lives -= t_fail
            next_lives = rs.choice(
                             LIFETIME_DISTS["Lifetime (hrs)"], size=3,
                             p=LIFETIME_DISTS["Probability"]).astype(float)
            delay = rs.choice(
                        DELAY_DISTS["Delay (min)"],
                        p=DELAY_DISTS["Probability"])
            if replace_all:
                num = 3
                lives = next_lives.copy()
            else:
                num = 1
                idx = np.argmin(lives)
                lives[idx] = next_lives[0]
            downtime = delay + REPLACEMENT_TIME[num]
            c, *_    = calculate_costs(downtime, num)
            total_cost += c
        return total_cost / total_hours

    rates_curr = np.array([simulate_rate_trial(False) for _ in range(int(n_trials))])
    rates_prop = np.array([simulate_rate_trial(True)  for _ in range(int(n_trials))])

    # Average rates table & bar chart
    rate_table = pd.DataFrame({
        "Policy": ["Current", "Proposed"],
        "Avg Cost per Hour ($/hr)": [rates_curr.mean(), rates_prop.mean()]
    }).set_index("Policy")
    st.write("**Average Cost per Hour**")
    st.table(rate_table)

    fig_rate, ax_rate = plt.subplots()
    ax_rate.bar(rate_table.index, rate_table["Avg Cost per Hour ($/hr)"])
    ax_rate.set_ylabel("Cost per Hour ($/hr)")
    ax_rate.set_title("Average Cost Rate by Policy")
    st.pyplot(fig_rate)

    # Boxplot of rates
    fig_box, ax_box = plt.subplots()
    ax_box.boxplot([rates_curr, rates_prop], labels=["Current", "Proposed"])
    ax_box.set_ylabel("Cost per Hour ($/hr)")
    ax_box.set_title("Cost Rate Distribution")
    st.pyplot(fig_box)

    # Paired t-test (one-tailed)
    t_rel, p_two = ttest_rel(rates_curr, rates_prop)
    p_one = p_two/2 if t_rel > 0 else 1 - p_two/2
    alpha = 0.01
    st.write(f"Paired t-test: t = {t_rel:.3f}, one-tailed p = {p_one:.3e}")
    if (rates_curr.mean() > rates_prop.mean()) and (p_one < alpha):
        st.success("Proposed Policy has significantly lower cost per hour (α=0.01).")
    else:
        st.info("No significant advantage in cost per hour at α=0.01.")
