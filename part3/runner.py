#!/usr/bin/env python3
import re
import time
import csv
from pathlib import Path
from topo_wordcount import make_net
import subprocess

# Config
NUM_CLIENTS_VALUES = [10]
RUNS_PER_SETTING = 5
SERVER_CMD = "python3 server.py --config config.json"
CLIENT_CMD_TMPL = "python3 -u client.py --config config.json --quiet --c {c}"

RESULTS_CSV = Path("results.csv")

def modify_config(param, value):
    import json
    with open("config.json", "r") as f:
        cfg = json.load(f)
    cfg[param] = value
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)

def main():
    # always overwrite file fresh
    with RESULTS_CSV.open("w", newline="") as f:
        csv.writer(f).writerow(["num_clients", "run", "elapsed_ms"])

    num_clients = 10
    net = make_net(num_clients)
    net.start()
    h_server = net.get('sv')
    srv = h_server.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
    for c in range(1,11):
        time.sleep(0.5)  # let server bind
        for r in range(1, RUNS_PER_SETTING + 1):
            procs = []
            outputs = []
            modify_config("num_clients", num_clients)
            # launch clients concurrently
            for i in range(1,num_clients+1):
                h_client = net.get(f'h{i}')
                cmd = CLIENT_CMD_TMPL.format(c=c)
                p = h_client.popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                procs.append(p)

            # collect results
            for p in procs:
                out = p.stdout.read()
                outputs.append(out.decode())

            # terminate clients
            for p in procs:
                p.terminate()

            times = []
            for out in outputs:
                m = re.search(r"ELAPSED_MS:(\d+\.?\d*)", out)
                if m:
                    times.append(float(m.group(1)))

            if times:
                avg = sum(times) / len(times)
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([num_clients, r, avg])
                print(f"c={c} run={r} elapsed_per_client_per_message_ms={avg:.2f}")
            else:
                print(f"[warn] No times collected for c={c}, run={r}")

    srv.terminate()
    net.stop()

if __name__ == "__main__":
    main()
