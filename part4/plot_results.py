#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import math
import sys

INPUT_CSV = Path("results.csv")
OUTPUT_PLOT = "p4_plot.png"

if not INPUT_CSV.exists():
    print(f"[ERROR] {INPUT_CSV} not found")
    sys.exit(1)

# Load CSV
df = pd.read_csv(INPUT_CSV)

# possible column names for c and jfi
c_candidates = ["c", "c_value", "C", "c_val"]
jfi_candidates = ["jfi", "JFI", "JFI_value"]

def find_column(candidates, df):
    for c in candidates:
        if c in df.columns:
            return c
    return None

c_col = find_column(c_candidates, df)
jfi_col = find_column(jfi_candidates, df)

if c_col is None or jfi_col is None:
    print("[ERROR] Could not find required columns in CSV.")
    print("Found columns:", list(df.columns))
    print("Expected c column one of:", c_candidates)
    print("Expected jfi column one of:", jfi_candidates)
    sys.exit(1)

# Make sure c is numeric
df[c_col] = pd.to_numeric(df[c_col], errors="coerce")
df[jfi_col] = pd.to_numeric(df[jfi_col], errors="coerce")

# Drop rows with missing values
df = df.dropna(subset=[c_col, jfi_col])

if df.empty:
    print("[ERROR] No valid data after cleaning.")
    sys.exit(1)

# Group by c and compute mean, std, count
agg = df.groupby(c_col)[jfi_col].agg(["mean", "std", "count"]).reset_index().sort_values(by=c_col)

# Compute SEM and 95% CI (use normal approximation)
agg["sem"] = agg["std"] / agg["count"].pow(0.5)
agg["ci95"] = 1.96 * agg["sem"]

# If count == 1, std will be NaN; replace ci95 with 0
agg["ci95"] = agg["ci95"].fillna(0.0)

# Plot
plt.figure(figsize=(8, 5))
plt.errorbar(agg[c_col], agg["mean"], yerr=agg["ci95"], fmt='o-', capsize=4)
plt.xlabel("c (greedy requests)")
plt.ylabel("Jain's Fairness Index (JFI)")
plt.ylim(0, 1.2)
plt.title("JFI vs c (mean ± 95% CI)")
plt.grid(True)
plt.tight_layout()
plt.savefig(OUTPUT_PLOT, dpi=180)
print(f"Saved plot to {OUTPUT_PLOT}")
