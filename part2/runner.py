# #!/usr/bin/env python3
# import time
# import json
# import subprocess
# from pathlib import Path
# import sys
# from topo_wordcount import create_network

# SERVER_CMD = "python3 server.py --config config.json"
# CLIENT_CMD = "python3 client.py --config config.json"

# base_config = json.loads(Path("config.json").read_text())
# num_clients = base_config["num_clients"]

# print(f"--- Starting demo with {num_clients} concurrent clients ---")

# #Mininet
# net = create_network(num_clients=num_clients)
# net.start()

# server_host = net.get('server')
# client_hosts = []
# for i in range(1, num_clients + 1):
#     name = f'client{i}'
#     host = net.get(name)
#     client_hosts.append(host)

# # Start server
# server_proc = server_host.popen(SERVER_CMD, shell=True)
# time.sleep(2) # Wait for server to bind

# if server_proc.poll() is None:  # still running → started successfully
#     print(f"[DEBUG] server_proc process started successfully (PID: {server_proc.pid})")
# else:
#     print(f"[ERROR] server_proc failed to start. Return code: {server_proc.returncode}")
#     net.stop()
#     sys.exit(1)

# start_time = time.time()

# # Start clients concurrently
# print("Starting client processes on h_client1 through h_client...")
# client_procs = []
# for i, client in enumerate(client_hosts, 1): #i starts at 1
#     proc = client.popen("python3 client.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     client_procs.append(proc)

# # Wait for all clients to finish and print their output
# for i, proc in enumerate(client_procs, 1):
#     stdout, stderr = proc.communicate() #communicate waits for each process in sequence
#     print(f"\n--- Output from Client {i} ---")
#     print(stdout)
#     if stderr:
#         print(f"Errors:\n{stderr}")
#     print(f"Client {i} completed with return code {proc.returncode}")

# end_time = time.time()
# total_time = end_time - start_time

# print(f"All {num_clients} clients completed in {total_time:.2f} seconds")

# # Clean up
# print("\nDemo finished. Shutting down...")
# server_proc.terminate()
# time.sleep(0.5)
# net.stop()
# print("\nExperiment Successful")


#!/usr/bin/env python3
import time
import json
import subprocess
from pathlib import Path
import sys
from topo_wordcount import make_net

SERVER_CMD = "python3 server.py --config config.json"
CLIENT_CMD = "python3 client.py --config config.json"

base_config = json.loads(Path("config.json").read_text())
num_clients = base_config["num_clients"]

print(f"--- Starting demo with {num_clients} concurrent clients ---")

#Mininet
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

# Start clients concurrently
print("Starting client processes on h_client1 through h_client...")
client_procs = [
    client_host.popen(
        CLIENT_CMD,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    for _ in range(num_clients)
]

# Wait for all clients to finish and print their output
for i, proc in enumerate(client_procs, 1):
    stdout, stderr = proc.communicate() #communicate waits for each process in sequence
    print(f"\n--- Output from Client {i} ---")
    print(stdout.decode())
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
