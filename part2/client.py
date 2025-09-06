#!/usr/bin/env python3
import argparse
import socket
import time
import json

def parse_config(filename):
    with open(filename, "r") as f:
        return json.load(f)

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
    parser.add_argument("--quiet", action="store_true", help="Toggle verbose output off")
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

    server_ip = config["server_ip"]
    server_port = int(config["server_port"])
    p = int(config.get("p", "0"))
    k = int(config.get("k", "5"))

    word_frequency = {}
    all_words_buffer = []

    # Create TCP socket and connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, server_port))
    except Exception as e:
        print(f"Connection failed: {e}")
        return 1
    
    start = time.perf_counter()
    while True:
        message = f"{p},{k}\n".encode('utf-8')

        sock.sendall(message)

        #It may be possible that data may come in chunks
        response_data = ""
        while not response_data.endswith('\n'):
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("Server closed connection unexpectedly.")
            response_data += chunk.decode('utf-8')

        response_line = response_data.strip() #Removes \n or spaces

        eof_received = False
        if response_line.endswith("EOF"):
            eof_received = True
            # Remove the "EOF" token and any trailing comma
            response_line = response_line[:-3].strip(',')

        if response_line:
            received_words = response_line.split(',')
            all_words_buffer.extend(received_words)

        if eof_received:
            break # Download is complete

        p += k

    sock.close()

    end_time = time.perf_counter()
    elapsed_ms = (end_time - start) * 1000
    print(f"ELAPSED_MS:{elapsed_ms}")

    for word in all_words_buffer:
        word_frequency[word] = word_frequency.get(word, 0) + 1

    if not args.quiet:
        print_freq(word_frequency)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
