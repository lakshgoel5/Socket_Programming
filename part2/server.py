#!/usr/bin/env python3
import socket
import sys
import json

def parse_config(filename):
    """Load config.json with server_ip and server_port"""
    with open(filename, "r") as f:
        return json.load(f)

def load_words(filename):
    """Load comma-separated words into a list, append EOF marker"""
    words = []
    with open(filename, "r") as f:
        for line in f:
            for w in line.strip().split(","):
                w = w.strip()
                if w:
                    words.append(w)
    words.append("EOF")
    return words

def handle_client(client_sock, word_list):
    """Process a single client request"""
    data = client_sock.recv(1024).decode().strip()
    if not data:
        return
    try:
        p_str, k_str = data.split(",")
        p, k = int(p_str), int(k_str)
    except Exception:
        print("Invalid client request:", data)
        return

    # Build response
    response = []
    for i in range(p, min(p+k, len(word_list))):
        response.append(word_list[i])
    if p + k >= len(word_list):
        response.append("EOF")
    msg = ",".join(response) + "\n"

    client_sock.sendall(msg.encode())

def main():
    config_file = "config.json"
    words_file = "words.txt"

    # parse args
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == "--config" and i+1 < len(args):
            config_file = args[i+1]
        if args[i] == "--words" and i+1 < len(args):
            words_file = args[i+1]

    config = parse_config(config_file)
    word_list = load_words(words_file)

    host = config["server_ip"]
    port = int(config["server_port"])

    # Create TCP socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(32)   # backlog large enough

    print(f"Server listening on {host}:{port}")

    while True:
        client_sock, addr = server_sock.accept()
        # Serve one client at a time (sequential)
        handle_client(client_sock, word_list)
        client_sock.close()

if __name__ == "__main__":
    main()
