#!/usr/bin/env python3
import re
import time
import csv
import json
from pathlib import Path
from statistics import mean

# --- Configuration ---
# The number of concurrent clients to test
CLIENT_COUNTS = [1, 5, 9, 13, 17, 21, 25, 29, 32]
RUNS_PER_COUNT = 5  # Number of times to repeat the experiment for each client count
SERVER_CMD = "python3 server.py --config config.json"
CLIENT_CMD = "python3 client.py --config config.json --quiet"
RESULTS_CSV = Path("results_part2.csv")

def modify_config(param, value):
    """Helper function to modify the shared config.json file."""
    with open("config.json", "r") as f:
        cfg = json.load(f)
    cfg[param] = value
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)

def main():
    # Prepare the CSV file with headers
    with RESULTS_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["num_clients", "run", "avg_completion_time_ms"])

    # Ensure a words.txt file exists for the server to read
    if not Path("words.txt").exists():
        Path("words.txt").write_text("word," * 5000)

    # --- Main Experiment Loop ---
    for n_clients in CLIENT_COUNTS:
        print(f"\n--- Testing with {n_clients} concurrent client(s) ---")

        # Set the number of clients in the config for the server's listen() backlog
        modify_config("num_clients", n_clients)

        for r in range(1, RUNS_PER_COUNT + 1):
            print(f"  Running iteration {r}/{RUNS_PER_COUNT}...")
            # Dynamically create the network with the required number of hosts
            # This is done inside the loop to ensure a clean state for each run
            from topo_wordcount import make_net
            net = make_net(n_clients=n_clients)
            net.start()

            # Get host objects from the running network
            server_host = net.get('h_server')
            client_hosts = [net.get(f'h_client{i}') for i in range(1, n_clients + 1)]

            # Start the server process in the background
            server_proc = server_host.popen(SERVER_CMD, shell=True)
            time.sleep(1) # Give the server a moment to start and bind to the port

            # Start all client processes concurrently in the background
            client_procs = [host.popen(CLIENT_CMD, shell=True) for host in client_hosts]

            # --- Data Collection ---
            run_times = []
            for i, proc in enumerate(client_procs):
                # Wait for the client process to finish and get its output
                out = proc.waitOutput()
                # Use regex to find the "ELAPSED_MS" value in the output
                match = re.search(r"ELAPSED_MS:([\d\.]+)", out)
                if match:
                    elapsed_ms = float(match.group(1))
                    run_times.append(elapsed_ms)
                else:
                    print(f"[WARN] No ELAPSED_MS found for client {i+1}. Raw output:\n{out}")

            # --- Cleanup and Data Logging ---
            server_proc.terminate()
            net.stop()

            if run_times:
                avg_time = mean(run_times)
                print(f"    Average completion time for this run: {avg_time:.2f} ms")
                # Write the aggregated result for this run to the CSV
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([n_clients, r, avg_time])
            else:
                print("[ERROR] No successful client runs were recorded.")
            time.sleep(0.5) # Small delay between runs

if __name__ == "__main__":
    main()
