#!/usr/bin/env python3
import csv
import socket
import json
import time
import argparse
from collections import Counter
import re

def parse_args():
    parser = argparse.ArgumentParser(description="Word Counting Client")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--k", type=str, help="Override k parameter")
    parser.add_argument("--p", type=str, help="Override p parameter")
    parser.add_argument("--quiet", action="store_true", help="Toggle verbose output off")
    parser.add_argument("--is_greedy", action="store_true", help="Set this client as the greedy client")
    parser.add_argument("--c", type=int, default=1, help="Number of requests to send in a batch for the greedy client")

    return parser.parse_args()

def load_config(filename="config.json"):
    with open(filename, "r") as f:
        return json.load(f)

def analyse(buffer):
    words = re.split(r'[,\n]+', buffer.strip())
    words = [w for w in words if w and w != "EOF"]
    return Counter(words)

def main():
    args = parse_args()
    cfg = load_config()
    if not cfg:
        return 1

    if args.k is not None:
        cfg["k"] = args.k
    if args.p is not None:
        cfg["p"] = args.p
    if args.c is not None:
        cfg["c"] = args.c
    

    server_ip = cfg["server_ip"]
    server_port = int(cfg["server_port"])
    k = int(cfg["k"])
    p = int(cfg["p"])
    is_greedy = args.is_greedy
    c = cfg["c"]

    start = time.perf_counter()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    requests_to_send = c if is_greedy else 1 # default c is 1
    all_data = ""
    while True:
        for _ in range(requests_to_send):
            msg = f"{p},{k}\n"
            sock.sendall(msg.encode())
            p += k

        responses_received = 0
        while responses_received < requests_to_send:
            try:
                data = sock.recv(1024)
            except socket.error:
                data = b""
            if not data:
                break

            chunk = data.decode()
            all_data += chunk

            responses_received += chunk.count("\n")  # each resp nds with newline, so receive till c newlines received

            if "EOF" in chunk:
                break

        if "EOF" in all_data:
            break
        
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"ELAPSED_MS:{elapsed_ms:.3f}")

    sock.close()

    analyse_result = analyse(all_data)

    if not cfg.get("quiet", False):
        for word, count in analyse_result.items():
            print(f"{word}, {count}")

if __name__ == "__main__":
    main()
