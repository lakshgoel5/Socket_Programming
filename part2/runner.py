#!/usr/bin/env python3
import re
import time
import csv
from pathlib import Path
from topo_wordcount import make_net
from mininet.cli import CLI

# Config
NUM_CLIENTS_VALUES = [2]
RUNS_PER_SETTING = 1
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

def main():
    with RESULTS_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["num_clients", "run", "client_id", "elapsed_ms"])

    net = make_net()
    net.start()

    h1 = net.get('h1')
    h2 = net.get('h2')

    if not Path("words.txt").exists():
        Path("words.txt").write_text("cat,bat,cat,dog,dog,emu,emu,emu,ant\n")

    try:
        for num_clients in NUM_CLIENTS_VALUES:
            for r in range(1, RUNS_PER_SETTING + 1):
                srv = h2.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
                time.sleep(2)

                # launch clients 
                procs = []
                for cid in range(num_clients):
                    cmd = CLIENT_CMD_TMPL
                    p = h1.popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    procs.append((cid, p))

                for cid, p in procs:
                    out, err = p.communicate()
                    out = out.decode()
                    m = re.search(r"ELAPSED_MS:([0-9]+(?:\.[0-9]+)?)", out)
                    print(out)
                    if not m:
                        print(f"[warn] Client {cid} gave no ELAPSED_MS. Raw:\n{out}")
                        continue
                    ms = float(m.group(1))  # <-- float instead of int
                    with RESULTS_CSV.open("a", newline="") as f:
                        csv.writer(f).writerow([num_clients, r, cid, ms])
                    print(f"clients={num_clients} run={r} client={cid} elapsed_ms={ms:.3f}")

                srv.terminate()
                time.sleep(0.2)

    finally:
        net.stop()

if __name__ == "__main__":
    import subprocess
    main()
