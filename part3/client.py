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
    parser.add_argument("--is_greedy", action="store_true", help="Set this client as the greedy client")
    parser.add_argument("--c", type=int, default=1, help="Number of requests to send in a batch for the greedy client")
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

    is_greedy = args.is_greedy
    c = max(1, int(args.c))  # ensure at least 1

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
    eof_received = False

    while not eof_received:
        # Determine how many requests to send in this batch
        requests_to_send = c if is_greedy else 1

        # Send requests back-to-back (or until EOF would be reached in client's logic)
        sent = 0
        for _ in range(requests_to_send):
            # prepare message and send
            message = f"{p},{k}\n".encode('utf-8')
            try:
                sock.sendall(message)
            except BrokenPipeError:
                # server closed connection unexpectedly
                eof_received = True
                break
            sent += 1
            p += k  # move offset as if the requests were accepted
        if sent == 0:
            break

        # For each request sent, read exactly one response line (server responds per request)
        for _ in range(sent):
            response_data = ""
            while not response_data.endswith('\n'):
                chunk = sock.recv(4096)
                if not chunk:
                    # server closed connection unexpectedly
                    eof_received = True
                    break
                response_data += chunk.decode('utf-8')
            if not response_data:
                break

            response_line = response_data.strip()

            if response_line.endswith("EOF"):
                eof_received = True
                response_line = response_line[:-3].strip(',')

            if response_line:
                received_words = [w for w in response_line.split(',') if w]
                all_words_buffer.extend(received_words)

            if eof_received:
                break

    try:
        sock.close()
    except Exception:
        pass

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
