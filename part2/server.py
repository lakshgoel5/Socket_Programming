#!/usr/bin/env python3
import socket
import sys
import json

def parse_config(filename):
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

def handle_client(client_socket, word_list):
    try:
        data = client_socket.recv(1024).decode()
        if not data.endswith('\n'):
            client_socket.sendall(b"EOF\n")
            return

        data = data.strip()
        parts = data.split(',')
        if len(parts) != 2:
            client_socket.sendall(b"EOF\n")
            return

        try:
            p = int(parts[0])
            k = int(parts[1])
        except ValueError:
            client_socket.sendall(b"EOF\n")
            return

        if p >= len(word_list):
            client_socket.sendall(b"EOF\n")
            return

        slice_end = p + k
        if slice_end > len(word_list):
            slice_end = len(word_list)

        response_words = word_list[p:slice_end]
        if response_words and response_words[-1] == "EOF":
            # Send words until EOF including it, suffixed by \n
            response = ','.join(response_words) + '\n'
        elif slice_end == len(word_list):
            # End reached without EOF in slice
            response = ','.join(response_words) + ',EOF\n'
        else:
            response = ','.join(response_words) + '\n'

        client_socket.sendall(response.encode())
    finally:
        client_socket.close()

def main():
    config = parse_config("config.json")
    if not config:
        return 1

    word_list = load_words(config.get("filename", "words.txt"))
    if not word_list:
        return 1

    server_ip = config.get("server_ip", "0.0.0.0")
    server_port = int(config.get("server_port", 5000))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((server_ip, server_port))
    server_socket.listen(1)
    print(f"Server listening on {server_ip}:{server_port}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection accepted from {addr}")
            handle_client(client_socket, word_list)
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
