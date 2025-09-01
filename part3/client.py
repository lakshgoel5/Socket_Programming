#!/usr/bin/env python3
import argparse
import socket
import time
import json

def parse_config(filename):
    """Parse JSON config file into a dictionary."""
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error reading config '{filename}': {e}")
        return {}

def analyse(buffer, freq):
    """
    Parses a comma-separated word string, counting frequency of each word until 'EOF'.
    """
    words = buffer.split(',')
    for word in words:
        key = word.strip()
        if key == 'EOF':
            break
        if key:
            freq[key] = freq.get(key, 0) + 1

def print_freq(freq):
    """
    Prints the frequency dictionary as 'word, count' lines.
    """
    items = list(freq.items())
    for i, (word, count) in enumerate(items):
        end_char = '\n' if i < len(items) - 1 else ''
        print(f"{word}, {count}", end=end_char)

def parse_args():
    parser = argparse.ArgumentParser(description="Word Counting Client")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--k", type=str, help="Override k parameter")
    parser.add_argument("--p", type=str, help="Override p parameter")
    parser.add_argument("--quiet", action="store_false", help="Toggle verbose output off")
    parser.add_argument("--c", type=int, default=1, help="Number of requests per client")
    return parser.parse_args()

def main():
    args = parse_args()
    config = parse_config(args.config)
    if not config:
        return 1

    if args.k is not None:
        config["k"] = args.k
    if args.p is not None:
        config["p"] = args.p
    c = args.c

    server_ip = config.get("server_ip")
    server_port = int(config.get("server_port", 0))
    p = config.get("p", "0")
    k = config.get("k", "5")

    if not server_ip or server_port == 0:
        print("Invalid server IP or port in configuration")
        return 1

    # Create TCP socket and connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, server_port))
    except Exception as e:
        print(f"Connection failed: {e}")
        return 1

    # message = f"{p},{k}\n".encode()
    # start = time.perf_counter()
    # sock.sendall(message)
    # buffer = sock.recv(1024).decode()
    # end = time.perf_counter()
    # elapsed_ms = (end - start) * 1000
    # print(f"ELAPSED_MS:{elapsed_ms}")

    responses = []
    
    start = time.perf_counter()

    for i in range(c):
        message = f"{p},{k}\n".encode()
        sock.sendall(message)
    for i in range(c):
        buffer = sock.recv(1024).decode()
        responses.append(buffer)

    end = time.perf_counter()

    elapsed_ms = ((end-start)/c) * 1000 # gives the time per request, for one client
    print(f"ELAPSED_MS: {elapsed_ms}")

    sock.close()

    for buffer in responses:
        freq = {}
        analyse(buffer, freq)
        if args.quiet:
            print_freq(freq)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
