#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv("results.csv")

# Jain's Fairness Index function
def jfi(values):
    values = values.to_numpy()  # ensure numpy array
    numerator = (values.sum())**2
    denominator = len(values) * (values**2).sum()
    return numerator / denominator if denominator != 0 else 0

# Group by c and compute JFI
jfi_df = df.groupby("c")["elapsed_ms"].apply(jfi).reset_index()
jfi_df.columns = ["c", "JFI"]  # rename for clarity

print(jfi_df)  # 👈 see values before plotting

# Plot
plt.figure()
plt.plot(jfi_df["c"].to_numpy(), jfi_df["JFI"].to_numpy(), marker='o')
plt.xlabel("c")
plt.ylabel("Jain's Fairness Index (JFI)")
plt.title("Fairness (JFI) vs. c")
plt.grid(True)
plt.savefig("p3_plot.png", bbox_inches="tight", dpi=180)
print("Saved p3_plot.png")
