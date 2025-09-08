#!/usr/bin/env python3

import json
import os
import time
import glob
import numpy as np
import csv
from statistics import mean
import re
from pathlib import Path
import argparse
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

OUTPUT_PLOT_JFI = "p3_plot.png"

RESULTS_CSV = Path("results.csv")
SERVER_CMD = "python3 server.py --config config.json"
CLIENT_CMD = "python3 client.py --config config.json --quiet"


class Runner:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.server_ip = self.config['server_ip']
        self.port = self.config['server_port']
        self.p = self.config['p']  # offset
        self.k = self.config['k']  # words per request

    def calculate_jfi(self, values):
        if not values:
            return 0.0
        n = len(values)
        s = sum(values)
        sq_sum = sum(v * v for v in values)
        return (s * s) / (n * sq_sum) if sq_sum > 0 else 0.0

    def cleanup_logs(self):
        """Clean old log files"""
        logs = glob.glob("logs/*.log")
        for log in logs:
            os.remove(log)
        print("Cleaned old logs")

    def run_experiment(self, n_clients, run_id, c):
        from topo_wordcount import make_net

        # always creates h1 (clients) and h2 (server)
        net = make_net()
        net.start()

        server_host = net.get('h1')
        client_host = net.get('h2')

        # start server
        server_proc = server_host.popen(SERVER_CMD, shell=True)
        time.sleep(2)

        if server_proc.poll() is not None:
            print("[ERROR] server failed to start")
            net.stop()
            return

        # launch all clients on h1
        greedy_cmd = f"{CLIENT_CMD} --is_greedy --c {c}"
        client_procs = []
        # first greedy
        client_procs.append(
            client_host.popen(
                greedy_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        )
        # remaining non-greedy clients
        for _ in range(n_clients - 1):
            client_procs.append(
                client_host.popen(
                    CLIENT_CMD,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            )

        run_times = []
        for proc in client_procs:
            out, _ = proc.communicate()
            if isinstance(out, bytes):
                out = out.decode('utf-8', errors='ignore')
            m = re.search(r"ELAPSED_MS:([\d\.]+)", out)
            if m:
                run_times.append(float(m.group(1)))

        # cleanup server
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()

        # cleanup clients
        for proc in client_procs:
            if proc.poll() is None:
                proc.kill()

        net.stop()

        # record results
        if run_times:
            avg_time = mean(run_times)
            jfi = self.calculate_jfi(run_times)
            # IMPORTANT: write row matching header ["num_clients","c","run","avg_completion_time_ms","jfi"]
            with RESULTS_CSV.open("a", newline="") as f:
                csv.writer(f).writerow([n_clients, c, run_id, avg_time, jfi])
            print(f"[INFO] n_clients={n_clients}, c={c}, run={run_id}, avg={avg_time:.2f}, jfi={jfi:.3f}")
        else:
            print(f"[WARN] No client times recorded for n_clients={n_clients}, c={c}, run={run_id}")

    def run_all(self, client_counts, runs_per_count, c_values):
        with RESULTS_CSV.open("w", newline="") as f:
            csv.writer(f).writerow(["num_clients", "c", "run", "avg_completion_time_ms", "jfi"])
        for c in c_values:
            for r in range(1, runs_per_count + 1):
                self.run_experiment(client_counts, r, c)

    def generate_plots(self):
        """
        Loads data from RESULTS_CSV and generates plots for completion time and JFI.
        Assumes CSV columns: num_clients, c, run, avg_completion_time_ms, jfi
        """
        if not RESULTS_CSV.exists():
            print(f"Error: Results file '{RESULTS_CSV}' not found.")
            print("Please run '--experiments' first.")
            return
        try:
            df = pd.read_csv(RESULTS_CSV)
            if df.empty:
                print(f"Error: Results file '{RESULTS_CSV}' is empty.")
                return
        except pd.errors.EmptyDataError:
            print(f"Error: Results file '{RESULTS_CSV}' is empty.")
            return

        # Quick check: print columns if something odd is happening
        # (comment out when stable)
        # print("DEBUG: CSV columns:", df.columns.tolist())

        # Ensure 'c' is numeric and sort by it
        df['c'] = pd.to_numeric(df['c'], errors='coerce')
        df = df.dropna(subset=['c']).copy()
        df['c'] = df['c'].astype(int)
        df = df.sort_values('c')

        # --- Data Aggregation by c ---
        agg_time = df.groupby("c")["avg_completion_time_ms"].agg(["mean", "std", "count"]).reset_index()
        agg_jfi = df.groupby("c")["jfi"].agg("mean").reset_index().rename(columns={"jfi": "mean_jfi"})
        agg_time["sem"] = agg_time["std"] / (agg_time["count"]**0.5)
        agg_time["ci95"] = 1.96 * agg_time["sem"]
        run_count = int(agg_time['count'].iloc[0]) if not agg_time.empty else 'N/A'

        # Convert columns to numpy arrays for plotting (avoids pandas indexing issues)
        x_time = agg_time["c"].to_numpy()
        y_time = agg_time["mean"].to_numpy()
        y_err = agg_time["ci95"].to_numpy()

        x_jfi = agg_jfi["c"].to_numpy()
        y_jfi = agg_jfi["mean_jfi"].to_numpy()

        # --- Plot Styling ---
        style_to_try = 'seaborn-v0_8-whitegrid'
        try:
            plt.style.use(style_to_try)
        except Exception:
            try:
                plt.style.use('seaborn-whitegrid')
            except Exception:
                pass

        # Plot: average completion time vs c (with 95% CI)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.errorbar(x_time, y_time, yerr=y_err, marker='o', linestyle='-', label="Avg completion time (ms)")
        ax.set_xlabel("Greedy batch size (c)", fontsize=12)
        ax.set_ylabel("Average completion time (ms)", fontsize=12)
        # pick a representative num_clients for the title (assumes constant)
        num_clients_for_title = int(df['num_clients'].iloc[0]) if 'num_clients' in df.columns and not df.empty else 'N/A'
        ax.set_title(f"Avg Completion Time vs c (num_clients={num_clients_for_title}, runs={run_count})", fontsize=14, fontweight='bold')
        ax.set_xticks(x_time)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        plt.tight_layout()
        time_plot = "p3_time_plot.png"
        plt.savefig(time_plot, dpi=180)
        print(f"Completion time plot saved to {time_plot}")

        # Plot: JFI vs c
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.plot(x_jfi, y_jfi, marker='s', linestyle='--', label="Average Jain's Fairness Index (JFI)")
        ax2.set_xlabel("Greedy batch size (c)", fontsize=12)
        ax2.set_ylabel("Jain's Fairness Index (JFI)", fontsize=12)
        ax2.set_title(f"Network Fairness vs Greedy Batch Size (num_clients={num_clients_for_title}, runs={run_count})", fontsize=14, fontweight='bold')
        ax2.set_xticks(x_jfi)
        ax2.set_ylim(0, 1.1)
        ax2.legend()
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_PLOT_JFI, dpi=180)
        print(f"JFI plot saved to {OUTPUT_PLOT_JFI}")





def main():
    # Setup argument parsing
    parser = argparse.ArgumentParser(description="Run network experiments or generate plots.")
    parser.add_argument(
        "--experiments",
        action="store_true",
        help="Run the experiments and generate results.csv."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate plots from existing results.csv."
    )
    args = parser.parse_args()

    # Conditional execution based on flags
    if args.experiments:
        runner = Runner()
        c_values = list(range(10,51,5))
        runner.run_all(client_counts=5, runs_per_count=5, c_values=c_values)

    if args.plot:
        runner = Runner()
        runner.generate_plots()

    # If no arguments are provided, show help message
    if not args.experiments and not args.plot:
        parser.print_help()


if __name__ == "__main__":
    main()