#!/usr/bin/env python3
import re
import time
import csv
from pathlib import Path
from topo_wordcount import make_net
from mininet.cli import CLI

# Config
NUM_CLIENTS_VALUES = [10]
RUNS_PER_SETTING = 5
C = 5
SERVER_CMD = "python3 server.py --config config.json"
CLIENT_CMD_TMPL = "python3 client.py --config config.json"

RESULTS_CSV = Path("results_part2.csv")

def modify_config(param, value):
    import json
    with open("config.json", "r") as f:
        cfg = json.load(f)
    cfg[param] = value
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)

def compute_jfi(elapsed_ms_list):
    if not elapsed_ms_list:
        return 0.0
    # convert to throughputs (requests per second) -- avoid division by zero
    throughputs = []
    for ms in elapsed_ms_list:
        if ms <= 0:
            continue
        throughputs.append(1000.0 / ms)  # 1000/ms -> # requests per second
    n = len(throughputs)
    if n == 0:
        return 0.0
    s = sum(throughputs)
    s2 = sum(x * x for x in throughputs)
    jfi = (s * s) / (n * s2) if s2 > 0 else 0.0
    return jfi

def main():
    # Prepare CSV (summary per run)
    with RESULTS_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["num_clients", "run", "c", "jfi"])

    net = make_net()
    net.start()

    h1 = net.get('h1')  # client host
    h2 = net.get('h2')  # server host

    # Ensure words.txt exists (shared FS)
    if not Path("words.txt").exists():
        Path("words.txt").write_text("cat,bat,cat,dog,dog,emu,emu,emu,ant\n")

    try:
        for num_clients in NUM_CLIENTS_VALUES:
            for r in range(1, RUNS_PER_SETTING + 1):
                # restart server fresh each run
                srv = h2.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
                time.sleep(2)  # give it time to bind

                # launch clients in parallel
                procs = []
                cmd = CLIENT_CMD_TMPL + f" --is_greedy --c {C}"
                p = h1.popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                procs.append((0, p))
                for cid in range(1, num_clients - 1):
                    cmd = CLIENT_CMD_TMPL
                    p = h1.popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    procs.append((cid, p))

                # collect results
                elapsed_list = []  # store elapsed_ms for each client that reported it
                for cid, p in procs:
                    out, err = p.communicate()
                    out = out.decode()
                    m = re.search(r"ELAPSED_MS:([0-9]+(?:\.[0-9]+)?)", out)
                    print(out)
                    if not m:
                        print(f"[warn] Client {cid} gave no ELAPSED_MS. Raw:\n{out}")
                        continue
                    ms = float(m.group(1))  # elapsed in milliseconds
                    elapsed_list.append(ms)
                    # still print per-client info for debugging
                    print(f"clients={num_clients} run={r} client={cid} c={C} elapsed_ms={ms:.3f}")

                # compute JFI from elapsed times (converted to throughput)
                jfi = compute_jfi(elapsed_list)

                # append summary row to CSV
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([num_clients, r, C, jfi])

                print(f"clients={num_clients} run={r} c={C} jfi={jfi:.6f}")

                srv.terminate()
                time.sleep(0.2)

    finally:
        net.stop()

if __name__ == "__main__":
    import subprocess
    main()
