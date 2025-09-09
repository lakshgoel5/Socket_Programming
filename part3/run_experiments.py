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

OUTPUT_PLOT = "p3_plot.png"

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
        """(Kept for compatibility) computes JFI directly on values (not used for ms -> throughput)."""
        if not values:
            return 0.0
        n = len(values)
        s = sum(values)
        sq_sum = sum(v * v for v in values)
        return (s * s) / (n * sq_sum) if sq_sum > 0 else 0.0

    def compute_jfi_from_ms(self, elapsed_ms_list):
        """Match original runner: convert elapsed ms -> throughput (1000/ms) then Jain's fairness index."""
        if not elapsed_ms_list:
            return 0.0
        throughputs = []
        for ms in elapsed_ms_list:
            if ms <= 0:
                continue
            throughputs.append(1000.0 / ms)
        n = len(throughputs)
        if n == 0:
            return 0.0
        s = sum(throughputs)
        s2 = sum(x * x for x in throughputs)
        jfi = (s * s) / (n * s2) if s2 > 0 else 0.0
        return jfi

    def cleanup_logs(self):
        """Clean old log files"""
        logs = glob.glob("logs/*.log")
        for log in logs:
            os.remove(log)
        print("Cleaned old logs")

    def run_experiment(self, n_clients, c, client_timeout=120):
        """
        Uses your working runner logic:
        - Starts Mininet net via make_net()
        - Starts server on h2
        - Launches greedy client first on h1, then remaining clients
        - Collects outputs and extracts ELAPSED_MS
        - Terminates server, kills leftover clients, stops net
        Returns: list of elapsed_ms (floats) collected from clients that reported them.
        """
        from topo_wordcount import make_net

        net = make_net()
        net.start()

        server_host = net.get('h2')
        client_host = net.get('h1')

        # start server on h2 (stdout/stderr left attached to host console)
        server_proc = server_host.popen(SERVER_CMD, shell=True)
        time.sleep(1.5)  # give it a short time to bind

        if server_proc.poll() is not None:
            print("[ERROR] server failed to start")
            try:
                net.stop()
            except Exception:
                pass
            return []

        # launch all clients on h1
        client_procs = []
        # Launch the greedy client first (client id 0)
        greedy_cmd = f"{CLIENT_CMD} --is_greedy --c {c}"
        client_procs.append((0, client_host.popen(greedy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)))

        # Launch non-greedy clients (ids 1..n_clients-1)
        for i in range(1, n_clients):
            client_procs.append((i, client_host.popen(f"{CLIENT_CMD}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)))

        run_times = []
        # Collect outputs (with timeout to avoid indefinite hang)
        for cid, proc in client_procs:
            try:
                out, err = proc.communicate(timeout=client_timeout)
            except subprocess.TimeoutExpired:
                print(f"[WARN] client {cid} timed out after {client_timeout}s; killing it")
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    out, err = proc.communicate(timeout=2)
                except Exception:
                    out = b""
                    err = b""
            if isinstance(out, bytes):
                out = out.decode('utf-8', errors='ignore')

            m = re.search(r"ELAPSED_MS:([0-9]+(?:\.[0-9]+)?)", out)
            if m:
                ms = float(m.group(1))
                run_times.append(ms)
                print(f"clients={n_clients} client={cid} c={c} elapsed_ms={ms:.3f}")
                # print entire client output for debugging if needed
                print(out)
            else:
                print(f"[warn] Client {cid} gave no ELAPSED_MS. Raw:\n{out}")

        # cleanup server
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                server_proc.kill()
            except Exception:
                pass

        # ensure remaining clients are killed
        for _, proc in client_procs:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

        # stop mininet
        try:
            net.stop()
        except Exception:
            pass

        return run_times

    def run_all(self, client_count, c_values, runs_per_setting=1):
        """
        For each c in c_values, run run_experiment runs_per_setting times,
        compute JFI for each run and append to RESULTS_CSV.
        """
        with RESULTS_CSV.open("w", newline="") as f:
            csv.writer(f).writerow(["num_clients", "run", "c_value", "jfi"])

        for c in c_values:
            for run_id in range(1, runs_per_setting + 1):
                run_times = self.run_experiment(client_count, c)
                jfi = self.compute_jfi_from_ms(run_times) if run_times else 0.0
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([client_count, run_id, c, jfi])
                print(f"[INFO] client_count={client_count} c={c} run={run_id} jfi={jfi:.3f}")

    def generate_plots(self, results_csv=RESULTS_CSV, output_plot=OUTPUT_PLOT):
        """
        Simple plot: read results CSV (num_clients, run, c_value, jfi) and plot jfi vs c_value.
        If multiple runs present, plot the average jfi per c_value.
        """
        if not results_csv.exists():
            print("[ERROR] results CSV not found:", results_csv)
            return

        df = pd.read_csv(results_csv, header=0)
        # When CSV rows are [num_clients, run, c_value, jfi] as we write
        if df.shape[1] < 4:
            print("[ERROR] unexpected results CSV format")
            return

        # Rename columns if needed
        df.columns = ['num_clients', 'run', 'c_value', 'jfi']
        grouped = df.groupby('c_value')['jfi'].mean().reset_index()

        plt.figure(figsize=(8, 5))
        plt.plot(grouped['c_value'], grouped['jfi'], marker='o')
        plt.xlabel('c (greedy requests)')
        plt.ylabel('Jain Fairness Index (average over runs)')
        plt.title('JFI vs c')
        plt.grid(True)
        plt.savefig(output_plot)
        print(f"[INFO] saved plot to {output_plot}")


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
    parser.add_argument(
        "--clients",
        type=int,
        default=10,
        help="Number of clients to run in experiments"
    )
    parser.add_argument(
        "--cmin",
        type=int,
        default=1,
        help="min c value for sweep (inclusive)"
    )
    parser.add_argument(
        "--cmax",
        type=int,
        default=90,
        help="max c value for sweep (inclusive)"
    )
    parser.add_argument(
        "--cstep",
        type=int,
        default=10,
        help="step for c sweep"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="repetitions per c value"
    )
    args = parser.parse_args()

    if args.experiments:
        runner = Runner()
        c_values = list(range(args.cmin, args.cmax + 1, args.cstep))
        runner.run_all(client_count=args.clients, c_values=c_values, runs_per_setting=args.runs)

    if args.plot:
        runner = Runner()
        runner.generate_plots()

    if not args.experiments and not args.plot:
        parser.print_help()


if __name__ == "__main__":
    main()
