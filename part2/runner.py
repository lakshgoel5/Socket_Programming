#!/usr/bin/env python3
import re
import time
import csv
from pathlib import Path
from topo_wordcount import make_net

# Config
NUM_CLIENTS_VALUES = [1, 4, 8, 12, 16, 20, 24, 28, 32]
RUNS_PER_SETTING = 5
SERVER_CMD = "./server --config config.json"
CLIENT_CMD_TMPL = "./client --config config.json --quiet"

RESULTS_CSV = Path("results_part2.csv")

def main():
    # always overwrite file fresh
    with RESULTS_CSV.open("w", newline="") as f:
        csv.writer(f).writerow(["num_clients", "run", "avg_elapsed_ms"])

    net = make_net()
    net.start()

    h_server = net.get('h2')
    srv = h_server.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
    time.sleep(0.5)  # let server bind

    try:
        for num_clients in NUM_CLIENTS_VALUES:
            for r in range(1, RUNS_PER_SETTING + 1):
                procs = []
                outputs = []

                # launch clients concurrently
                for i in range(num_clients):
                    h_client = net.get('h1')  # or h1,h3,h4 if you made multiple hosts
                    p = h_client.popen(CLIENT_CMD_TMPL, shell=True, stdout=True, stderr=True)
                    procs.append(p)

                # collect results
                for p in procs:
                    out, _ = p.communicate()
                    outputs.append(out.decode())

                times = []
                for out in outputs:
                    m = re.search(r"ELAPSED_MS:(\d+\.?\d*)", out)
                    if m:
                        times.append(float(m.group(1)))

                if times:
                    avg = sum(times) / len(times)
                    with RESULTS_CSV.open("a", newline="") as f:
                        csv.writer(f).writerow([num_clients, r, avg])
                    print(f"num_clients={num_clients} run={r} avg_elapsed_ms={avg:.2f}")
                else:
                    print(f"[warn] No times collected for num_clients={num_clients}, run={r}")

    finally:
        srv.terminate()
        net.stop()

if __name__ == "__main__":
    main()
