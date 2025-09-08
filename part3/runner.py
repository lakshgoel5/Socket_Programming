#!/usr/bin/env python3
import time
import json
import subprocess
from pathlib import Path
import sys
from topo_wordcount import make_net

SERVER_CMD = "python3 server.py --config config.json"
CLIENT_CMD_BASE = "python3 client.py --config config.json"

base_config = json.loads(Path("config.json").read_text())
num_clients = base_config["num_clients"]
c = int(base_config.get("c", 1))  # desired greedy batch size

print(f"--- Starting demo with {num_clients} concurrent clients ---")

# Mininet
net = make_net()
net.start()

server_host = net.get('h1')
client_host = net.get('h2')

# Start server
server_proc = server_host.popen(SERVER_CMD, shell=True)
time.sleep(2) # Wait for server to bind

if server_proc.poll() is None:  # still running → started successfully
    print(f"[DEBUG] server_proc process started successfully (PID: {server_proc.pid})")
else:
    print(f"[ERROR] server_proc failed to start. Return code: {server_proc.returncode}")
    net.stop()
    sys.exit(1)

start_time = time.time()

# Start clients concurrently: one greedy client, rest normal
client_procs = []

# Greedy client (first)
greedy_cmd = f"{CLIENT_CMD_BASE} --is_greedy --c {c}"
client_procs.append(
    client_host.popen(
        greedy_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
)

# Non-greedy clients
for _ in range(num_clients - 1):
    client_procs.append(
        client_host.popen(
            CLIENT_CMD_BASE,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    )

# Wait for all clients to finish and print their output
for i, proc in enumerate(client_procs, 1):
    stdout, stderr = proc.communicate()
    # outputs are bytes; decode for printing
    if isinstance(stdout, bytes):
        try:
            decoded = stdout.decode()
        except Exception:
            decoded = stdout.decode(errors='ignore')
    else:
        decoded = stdout
    print(f"\n--- Output from Client {i} ---")
    print(decoded)
    if stderr:
        print(f"Errors:\n{stderr}")
    print(f"Client {i} completed with return code {proc.returncode}")

end_time = time.time()
total_time = end_time - start_time

print(f"All {num_clients} clients completed in {total_time:.2f} seconds")

# Clean up
print("\nDemo finished. Shutting down...")
server_proc.terminate()
time.sleep(0.5)
net.stop()
print("\nExperiment Successful")