#!/usr/bin/env python3
import socket
import sys
import json
import time

def parse_config(filename):
    with open(filename, "r") as f:
        return json.load(f)

def analyse(buffer):
    freq = {}
    for word in buffer.strip().split(","):
        word = word.strip()
        if word == "EOF" or not word:
            continue
        freq[word] = freq.get(word, 0) + 1
    return freq

def main():
    config_file = "config.json"
    k_override = None
    p_override = None
    quiet = True

    # parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--config" and i+1 < len(args):
            config_file = args[i+1]; i += 2; continue
        if args[i] == "--k" and i+1 < len(args):
            k_override = args[i+1]; i += 2; continue
        if args[i] == "--p" and i+1 < len(args):
            p_override = args[i+1]; i += 2; continue
        if args[i] == "--quiet":
            quiet = False; i += 1; continue
        i += 1

    config = parse_config(config_file)
    host = config["server_ip"]
    port = int(config["server_port"])
    k = k_override if k_override else config["k"]
    p = p_override if p_override else config["p"]

    # connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    msg = f"{p},{k}\n"
    start = time.time()
    sock.sendall(msg.encode())

    data = sock.recv(4096).decode()
    elapsed = (time.time() - start) * 1000.0  # ms
    print(f"ELAPSED_MS:{elapsed:.3f}")

    sock.close()

    if not quiet:
        freq = analyse(data)
        for w, c in freq.items():
            print(f"{w}, {c}")

if __name__ == "__main__":
    main()
