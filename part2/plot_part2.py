#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

CSV_FILE = "results_part2.csv"
OUTPUT_PNG = "p2_plot.png"

def main():
    df = pd.read_csv(CSV_FILE)

    # group by num_clients and compute mean elapsed_ms
    grouped = df.groupby("num_clients")["elapsed_ms"].mean().reset_index()

    # convert to numpy arrays (avoids indexing issues)
    x = grouped["num_clients"].to_numpy()
    y = grouped["elapsed_ms"].to_numpy()

    # Plot
    plt.plot(x, y, "-o")
    plt.xlabel("Number of clients")
    plt.ylabel("Average completion time per client (ms)")
    plt.title("Part 2: Average completion time per client vs. number of clients")
    plt.grid(True)
    plt.savefig(OUTPUT_PNG, dpi=150)
    print(f"Plot saved to {OUTPUT_PNG}")

if __name__ == "__main__":
    main()
