#!/usr/bin/env python3
import json
import os
import time
import glob
import re
import csv
import subprocess
from pathlib import Path
from topo_wordcount import make_net

RESULTS_CSV = Path("results.csv")
SERVER_CMD = "python3 -u server.py --config config.json"
CLIENT_CMD = "python3 client.py --config config.json"

class Runner:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        # Not strictly needed unless used
        self.server_ip = self.config.get('server_ip', '127.0.0.1')
        self.port = self.config.get('server_port', 8000)

    def compute_jfi_from_ms(self, elapsed_ms_list):
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
        return (s * s) / (n * s2) if s2 > 0 else 0.0

    def run_experiment(self, n_clients, c):
        net = make_net()
        net.start()

        server_host = net.get('h2')
        client_host = net.get('h1')

        # start server on h2
        server_proc = server_host.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
        time.sleep(2)

        if server_proc.poll() is not None:
            print("[ERROR] server failed to start")
            try:
                net.stop()
            except Exception:
                pass
            return []

        # launch greedy client first
        client_procs = []
        greedy_cmd = f"{CLIENT_CMD} --is_greedy --c {c}"
        client_procs.append((0, client_host.popen(greedy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)))
        # launch other clients
        for i in range(1, n_clients):
            client_procs.append((i, client_host.popen(CLIENT_CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)))

        run_times = []
        for cid, proc in client_procs:
            try:
                out, err = proc.communicate()
            except subprocess.TimeoutExpired:
                print(f"[warn] client {cid} timed out, killing")
                try:
                    proc.kill()
                except Exception:
                    pass
                continue
            out = out.decode('utf-8', errors='ignore')
            m = re.search(r"ELAPSED_MS:([0-9]+(?:\.[0-9]+)?)", out) 
            if m:
                ms = float(m.group(1))
                run_times.append(ms)
                print(f"clients={n_clients} client={cid} c={c} elapsed_ms={ms:.3f}")
            else:
                print(f"[warn] Client {cid} gave no ELAPSED_MS. Raw:\n{out[:300]}")

        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except Exception:
            try:
                server_proc.kill()
            except Exception:
                pass

        for _, proc in client_procs:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

        try:
            net.stop()
        except Exception:
            pass

        return run_times

    def run_all(self, client_count, c_values, runs_per_setting=1):
        with RESULTS_CSV.open("w", newline="") as f:
            csv.writer(f).writerow(["num_clients", "run", "c_value", "jfi"])
        for c in c_values:
            for run_id in range(1, runs_per_setting + 1):
                run_times = self.run_experiment(client_count, c)
                jfi = self.compute_jfi_from_ms(run_times) if run_times else 0.0
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([client_count, run_id, c, jfi])
                print(f"[INFO] client_count={client_count} c={c} run={run_id} jfi={jfi:.3f}")

def main():
    runner = Runner()
    c_values = list(range(11, 91, 10)) #run for c values at intervals of 10
    runner.run_all(client_count=10, c_values=c_values, runs_per_setting=1)

if __name__ == "__main__":
    main()
