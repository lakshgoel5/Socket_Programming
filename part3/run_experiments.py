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

    def run_experiment(self, n_clients, c):
        from topo_wordcount import make_net

        # always creates h1 (clients) and h2 (server)
        net = make_net()
        net.start()

        server_host = net.get('h2')
        client_host = net.get('h1')

        # start server
        server_proc = server_host.popen(SERVER_CMD, shell=True)
        time.sleep(2)

        if server_proc.poll() is not None:
            print("[ERROR] server failed to start")
            net.stop()
            return []

        # launch all clients on h1
        client_procs = []
        # Launch the greedy client first
        client_procs.append(
            client_host.popen(f"{CLIENT_CMD} --is_greedy --c {c}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        )
        # Launch the non-greedy clients
        for i in range(n_clients - 1):
            client_procs.append(
                client_host.popen(f"{CLIENT_CMD}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        return run_times

    def run_all(self, client_count, c_values):
        with RESULTS_CSV.open("w", newline="") as f:
            csv.writer(f).writerow(["num_clients", "c_value", "jfi"])
        for c in c_values:
            run_times = self.run_experiment(client_count, c)
            if run_times:
                jfi = self.calculate_jfi(run_times)
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([client_count, c, jfi])
                print(f"[INFO] c={c}, jfi={jfi:.3f}")
            else:
                print(f"[WARN] No client times recorded for c={c}")



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
        c_values = list(range(10,101,10))
        runner.run_all(client_count=5, c_values=c_values)

    if args.plot:
        runner = Runner()
        runner.generate_plots()

    # If no arguments are provided, show help message
    if not args.experiments and not args.plot:
        parser.print_help()


if __name__ == "__main__":
    main()



# #!/usr/bin/env python3
# import re
# import time
# import csv
# from pathlib import Path
# from topo_wordcount import make_net
# import subprocess
# import numpy as np

# # Config
# C_VALUES = range(1, 51, 5)      # c = 1..10
# RUNS_PER_C = 1
# NUM_CLIENTS = 10
# SERVER_CMD = "python3 server.py --config config.json"
# CLIENT_CMD_TMPL = "python3 client.py --config config.json --quiet"

# RESULTS_CSV = Path("results_part3.csv")

# def jains_fairness_index(times):
#     arr = np.array(times, dtype=float)
#     num = (arr.sum()) ** 2
#     den = len(arr) * (arr**2).sum()
#     return num / den if den > 0 else 0.0

# def main():
#     # Prepare CSV
#     with RESULTS_CSV.open("w", newline="") as f:
#         w = csv.writer(f)
#         w.writerow(["c", "run", "client_id", "elapsed_ms", "jfi"])

#     net = make_net()
#     net.start()

#     h1 = net.get('h1')  # client host
#     h2 = net.get('h2')  # server host

#     if not Path("words.txt").exists():
#         Path("words.txt").write_text("cat,bat,cat,dog,dog,emu,emu,emu,ant\n")

#     try:
#         for c in C_VALUES:
#             for r in range(1, RUNS_PER_C + 1):
#                 # restart server fresh each run
#                 srv = h2.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
#                 time.sleep(2)

#                 procs = []
#                 # launch 1 greedy client
#                 greedy_cmd = CLIENT_CMD_TMPL + f" --is_greedy --c {c}"
#                 p = h1.popen(greedy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#                 procs.append((0, p, True))
#                 # launch 9 normal clients
#                 for cid in range(NUM_CLIENTS - 1):
#                     cmd = CLIENT_CMD_TMPL
#                     p = h1.popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#                     procs.append((cid+1, p, False))

#                 times = []
#                 # collect results
#                 for cid, p, is_greedy in procs:
#                     out, err = p.communicate()
#                     out = out.decode()
#                     m = re.search(r"ELAPSED_MS:([0-9]+(?:\.[0-9]+)?)", out)
#                     if not m:
#                         print(f"[warn] Client {cid} gave no ELAPSED_MS. Raw:\n{out}")
#                         continue
#                     ms = float(m.group(1))
#                     times.append(ms)

#                 # compute fairness
#                 jfi = jains_fairness_index(times) if times else 0.0

#                 # write all client times + jfi
#                 for cid, ms in enumerate(times):
#                     with RESULTS_CSV.open("a", newline="") as f:
#                         csv.writer(f).writerow([c, r, cid, ms, jfi])
#                 print(f"c={c} run={r} JFI={jfi:.3f}")

#                 srv.terminate()
#                 time.sleep(0.2)

#     finally:
#         net.stop()

# if __name__ == "__main__":
#     main()
