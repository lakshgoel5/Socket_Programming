#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_FILE = "results.csv"
OUTPUT_PLOT = "p2_plot.png"

# Check if the results file exists
if not Path(RESULTS_FILE).exists():
    print(f"Error: Results file '{RESULTS_FILE}' not found.")
    print("Please run the experiments first using 'make plot' or 'sudo python3 run_experiments.py'")
    exit(1)

# Load the data using pandas
df = pd.read_csv(RESULTS_FILE)

# Group data by the number of clients and calculate statistics
# We need the mean, standard deviation (std), and count for confidence intervals
agg = df.groupby("num_clients")["avg_completion_time_ms"].agg(["mean", "std", "count"]).reset_index()

# Calculate the 95% confidence interval
# CI = 1.96 * (std / sqrt(count))
agg["sem"] = agg["std"] / (agg["count"]**0.5) # Standard Error of the Mean
agg["ci95"] = 1.96 * agg["sem"]

# --- Plotting ---
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6))

# Create an error bar plot
ax.errorbar(
    agg["num_clients"],
    agg["mean"],
    yerr=agg["ci95"],
    fmt='o-',          # Format: circles connected by a line
    capsize=5,         # Width of the error bar caps
    label="Average Time ± 95% CI",
    color='b',
    markerfacecolor='lightblue',
    markersize=8
)

# Set plot labels and title
ax.set_xlabel("Number of Concurrent Clients", fontsize=12)
ax.set_ylabel("Average Completion Time per Client (ms)", fontsize=12)
ax.set_title(f"Server Performance vs. Number of Clients (n={agg['count'].iloc[0]} runs)", fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, which='both', linestyle='--', linewidth=0.5)

# Ensure x-axis ticks are integers for client counts
ax.set_xticks(agg["num_clients"])
plt.xticks(rotation=45) # Rotate for better readability if crowded

# Save the plot to a file
plt.tight_layout()
plt.savefig(OUTPUT_PLOT, dpi=180)

print(f"Plot saved to {OUTPUT_PLOT}")
