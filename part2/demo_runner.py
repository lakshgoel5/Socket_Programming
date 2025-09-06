#!/usr/bin/env python3
import time
import json
import subprocess
from pathlib import Path
from topo_wordcount import create_network

NUM_DEMO_CLIENTS = 4
SERVER_CMD = "python3 server.py --config demo_config.json"
CLIENT_CMD = "python3 client.py --config demo_config.json"

def main():
    print(f"--- Starting demo with {NUM_DEMO_CLIENTS} concurrent clients ---")

    # Create a separate config file for the demo to avoid conflicts
    # with the main experiment's config.json
    base_config = json.loads(Path("config.json").read_text())
    base_config["num_clients"] = NUM_DEMO_CLIENTS
    Path("demo_config.json").write_text(json.dumps(base_config, indent=2))

    net = create_network(num_clients=NUM_DEMO_CLIENTS)
    net.start()

    server_host = net.get('server')
    client_hosts = []
    for i in range(1, NUM_DEMO_CLIENTS + 1):
        name = f'client{i}'
        host = net.get(name)
        client_hosts.append(host)

    # Start server
    print("Starting server on server...")
    server_proc = server_host.popen(SERVER_CMD, shell=True)
    time.sleep(1) # Wait for server to bind

    # Start clients concurrently
    print("Starting client processes on h_client1 through h_client...")
    client_procs = []
    for i, client in enumerate(client_hosts, 1): #i starts at 1
        proc = client.popen("python3 client.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        client_procs.append((i, proc))

    # Wait for all clients to finish and print their output
    for i, proc in client_procs:
        stdout, stderr = proc.communicate() #communicate waits for each process in sequence
        print(f"\n--- Output from Client {i} ---")
        print(stdout)
        if stderr:
            print(f"Errors:\n{stderr}")

    # Clean up
    print("\nDemo finished. Shutting down...")
    server_proc.terminate()
    time.sleep(0.5)
    net.stop()

if __name__ == '__main__':
    main()
