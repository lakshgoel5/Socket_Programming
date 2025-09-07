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

OUTPUT_PLOT_JFI = "p2_plot.png"

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

    def run_experiment(self, n_clients, run_id):
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
        client_procs = [
            client_host.popen(
                CLIENT_CMD,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            for _ in range(n_clients)
        ]

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
            with RESULTS_CSV.open("a", newline="") as f:
                csv.writer(f).writerow([n_clients, run_id, avg_time, jfi])
            print(f"[INFO] n_clients={n_clients}, run={run_id}, avg={avg_time:.2f}, jfi={jfi:.3f}")
        else:
            print(f"[WARN] No client times recorded for n_clients={n_clients}, run={run_id}")

    def run_all(self, client_counts, runs_per_count):
        with RESULTS_CSV.open("w", newline="") as f:
            csv.writer(f).writerow(["num_clients", "run", "avg_completion_time_ms", "jfi"])
        for n in client_counts:
            for r in range(1, runs_per_count + 1):
                self.run_experiment(n, r)

    def generate_plots():
        """
        Loads data from RESULTS_CSV and generates plots for completion time and JFI.
        """
        if not RESULTS_CSV.exists():
            print(f"Error: Results file '{RESULTS_CSV}' not found.")
            print("Please run 'make experiments' first.")
            return
        try:
            df = pd.read_csv(RESULTS_CSV)
            if df.empty:
                print(f"Error: Results file '{RESULTS_CSV}' is empty.")
                return
        except pd.errors.EmptyDataError:
            print(f"Error: Results file '{RESULTS_CSV}' is empty.")
            return

        # --- Data Aggregation ---
        agg_time = df.groupby("num_clients")["avg_completion_time_ms"].agg(["mean", "std", "count"]).reset_index()
        agg_jfi = df.groupby("num_clients")["jfi"].agg("mean").reset_index()
        agg_time["sem"] = agg_time["std"] / (agg_time["count"]**0.5)
        agg_time["ci95"] = 1.96 * agg_time["sem"]
        run_count = agg_time['count'].iloc[0] if not agg_time.empty else 'N/A'

        # --- Plot Styling ---
        style_to_try = 'seaborn-v0_8-whitegrid'
        try:
            plt.style.use(style_to_try)
        except OSError:
            print(f"Warning: Style '{style_to_try}' not found. Trying 'seaborn-whitegrid'.")
            try:
                plt.style.use('seaborn-whitegrid')
            except OSError:
                print("Warning: Fallback style 'seaborn-whitegrid' not found. Using default style.")

        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.plot(agg_jfi["num_clients"], agg_jfi["mean"], marker='s', linestyle='--', label="Average Jain's Fairness Index (JFI)", color='g')
        ax2.set_xlabel("Number of Concurrent Clients", fontsize=12)
        ax2.set_ylabel("Jain's Fairness Index (JFI)", fontsize=12)
        ax2.set_title(f"Network Fairness vs. Number of Clients (n={run_count} runs)", fontsize=14, fontweight='bold')
        ax2.set_xticks(agg_jfi["num_clients"])
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
    if args.run:
        runner = Runner()
        client_counts = [1, 5, 9, 13, 17, 21, 25, 29, 32]
        runner.run_all(client_counts, runs_per_count=5)

    if args.plot:
        runner = Runner()
        runner.generate_plots()

    # If no arguments are provided, show help message
    if not args.run and not args.plot:
        parser.print_help()


if __name__ == "__main__":
    main()