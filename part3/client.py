# #!/usr/bin/env python3
# import argparse
# import socket
# import time
# import json

# def parse_config(filename):
#     with open(filename, "r") as f:
#         return json.load(f)

# def print_freq(freq):
#     """
#     Prints the frequency dictionary as 'word, count' lines.
#     """
#     items = list(freq.items())
#     for i, (word, count) in enumerate(items):
#         end_char = '\n' if i < len(items) - 1 else ''
#         print(f"{word}, {count}", end=end_char)

# def parse_args():
#     parser = argparse.ArgumentParser(description="Word Counting Client")
#     parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
#     parser.add_argument("--k", type=str, help="Override k parameter")
#     parser.add_argument("--p", type=str, help="Override p parameter")
#     parser.add_argument("--quiet", action="store_true", help="Toggle verbose output off")
#     parser.add_argument("--is_greedy", action="store_true", help="Set this client as the greedy client")
#     parser.add_argument("--c", type=int, default=1, help="Number of requests to send in a batch for the greedy client")
#     return parser.parse_args()

# def main():
#     args = parse_args()
#     config = parse_config(args.config)
#     if not config:
#         return 1

#     if args.k is not None:
#         config["k"] = args.k
#     if args.p is not None:
#         config["p"] = args.p
#     is_greedy = args.is_greedy
#     c = args.c

#     server_ip = config["server_ip"]
#     server_port = int(config["server_port"])
#     p = int(config.get("p", "0"))
#     k = int(config.get("k", "5"))

#     word_frequency = {}
#     all_words_buffer = []

#     # Create TCP socket and connect
#     try:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.connect((server_ip, server_port))
#     except Exception as e:
#         print(f"Connection failed: {e}")
#         return 1
    
#     start = time.perf_counter()
#     eof_received = False
#     total_requests_sent = 0
#     total_responses_received = 0

#         # In client.py, function main()

#     # --- NEW, EFFICIENT PIPELINED LOGIC ---

#     # 1. Prime the pipeline by sending the initial batch of requests
#     requests_to_send = c if is_greedy else 1
#     for _ in range(requests_to_send):
#         if eof_received: break # Should not happen here, but good practice
#         message = f"{p},{k}\n".encode('utf-8')
#         sock.sendall(message)
#         p += k
#         total_requests_sent += 1

#     # 2. Loop until all work is done
#     buffer = ""
#     while not eof_received:
#         # We must block and wait for data ONLY if our buffer is empty
#         if '\n' not in buffer:
#             try:
#                 chunk = sock.recv(4096)
#                 if not chunk:
#                     # Server closed connection unexpectedly
#                     break
#                 buffer += chunk.decode('utf-8')
#             except ConnectionError:
#                 break

#         # 3. Process ONE response from the buffer
#         if '\n' in buffer:
#             response_line, buffer = buffer.split('\n', 1)
#             response_line = response_line.strip()
#             total_responses_received += 1

#             if "EOF" in response_line:
#                 eof_received = True
#                 response_line = response_line.replace(",EOF", "").replace("EOF", "")

#             if response_line:
#                 received_words = response_line.split(',')
#                 all_words_buffer.extend(w for w in received_words if w)

#             # 4. For every response processed, send ONE new request to keep the pipe full.
#             # This is the key to high performance and true "greediness".
#             if not eof_received:
#                 message = f"{p},{k}\n".encode('utf-8')
#                 sock.sendall(message)
#                 p += k
#                 total_requests_sent += 1

#     sock.close()
#     end_time = time.perf_counter()
#     elapsed_ms = (end_time - start) * 1000
#     print(f"ELAPSED_MS:{elapsed_ms}")

#     for word in all_words_buffer:
#         word_frequency[word] = word_frequency.get(word, 0) + 1

#     if not args.quiet:
#         print_freq(word_frequency)

#     return 0

# if __name__ == "__main__":
#     import sys
#     sys.exit(main())


#!/usr/bin/env python3
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

    requests_to_send = c if is_greedy else 1
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
            responses_received += chunk.count("\n")  # each response ends with newline

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
