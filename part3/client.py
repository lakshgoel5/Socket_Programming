#!/usr/bin/env python3
import argparse
import socket
import time
import json
import sys
import errno

def parse_config(filename):
    with open(filename, "r") as f:
        return json.load(f)

def print_freq(freq):
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
    parser.add_argument("--retries", type=int, default=5, help="Reconnect retries on connection failure")
    return parser.parse_args()

def make_socket(server_ip, server_port, timeout=5.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((server_ip, server_port))
    return s

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
    c = max(1, int(args.c))
    max_retries = int(args.retries)

    word_frequency = {}
    all_words_buffer = []
    received_buffer = ""  # persistent between reconnects
    eof_received = False

    # Create initial socket (may fail and be retried below)
    sock = None
    try:
        sock = make_socket(server_ip, server_port)
    except Exception as e:
        # We'll attempt reconnects later when needed
        sock = None

    start = time.perf_counter()

    # Keep requesting until server signals EOF
    while not eof_received:
        requests_to_send = c if is_greedy else 1

        # ensure we have a connected socket before sending
        if sock is None:
            # try to reconnect up to max_retries
            retries = 0
            while retries < max_retries and sock is None:
                try:
                    sock = make_socket(server_ip, server_port)
                except Exception:
                    retries += 1
                    time.sleep(0.1 * retries)
            if sock is None:
                print("Failed to connect after retries; aborting.")
                break

        # send up to requests_to_send messages; stop early if connection dies
        sent = 0
        for _ in range(requests_to_send):
            message = f"{p},{k}\n".encode('utf-8')
            try:
                sock.sendall(message)
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                # connection died while sending; close and mark sock=None to reconnect
                try:
                    sock.close()
                except Exception:
                    pass
                sock = None
                break
            # only increment p after successful send
            sent += 1
            p += k

        if sent == 0:
            # nothing sent this iteration (connection died); loop will reconnect and retry
            continue

        # Read 'sent' responses (or stop early on EOF or connection close)
        processed = 0
        while processed < sent and not eof_received:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    # peer closed connection gracefully
                    try:
                        sock.close()
                    except Exception:
                        pass
                    sock = None
                    break
                received_buffer += chunk.decode('utf-8')

                # process complete lines
                while '\n' in received_buffer and processed < sent:
                    line, _, received_buffer = received_buffer.partition('\n')

                    # check EOF marker
                    if line.endswith("EOF"):
                        eof_received = True
                        line = line[:-3].strip(',')

                    if line:
                        received_words = [w for w in line.split(',') if w]
                        all_words_buffer.extend(received_words)

                    processed += 1

                    if eof_received:
                        break

            except socket.timeout:
                # No data right now; break to allow reconnect or resend if needed
                break
            except (ConnectionResetError, OSError) as e:
                # connection was reset; close and set sock to None to reconnect
                try:
                    sock.close()
                except Exception:
                    pass
                sock = None
                break

    # ensure socket closed
    try:
        if sock:
            sock.close()
    except Exception:
        pass

    end = time.perf_counter()
    elapsed_ms = (end - start) * 1000
    print(f"ELAPSED_MS:{elapsed_ms}")

    for word in all_words_buffer:
        word_frequency[word] = word_frequency.get(word, 0) + 1

    if not args.quiet:
        print_freq(word_frequency)

    return 0

if __name__ == "__main__":
    sys.exit(main())
