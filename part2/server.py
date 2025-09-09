#!/usr/bin/env python3
import socket
import json
import select

def load_config(filename="config.json"):
    with open(filename, "r") as f:
        return json.load(f)

def load_words(filename="words.txt"):
    words = []
    with open(filename, "r") as f:
        for line in f:
            for w in line.strip().split(","):
                w = w.strip()
                if w:
                    words.append(w)
    words.append("EOF")
    return words

def process_request(data, word_list):
    if not data:
        return "EOF\n"

    if data.endswith("\n"):
        data = data[:-1]

    try:
        p_str, k_str = data.split(",")
        p, k = int(p_str), int(k_str)
    except Exception:
        return "EOF\n"

    n = len(word_list)
    response_words = []
    pos = p
    for pos in range(p, min(p + k, n)):
        response_words.append(word_list[pos])

    if pos < p + k - 1:  # not enough words
        response_words.append("EOF")

    return ",".join(response_words) + "\n"

def main():
    cfg = load_config()
    word_list = load_words(cfg.get("filename", "words.txt"))

    server_ip = cfg["server_ip"]
    server_port = int(cfg["server_port"])

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((server_ip, server_port))
    server_sock.listen(32) 
    server_sock.setblocking(False)

    sockets = [server_sock] 

    print(f"Concurrent server listening on {server_ip}:{server_port}")

    while True:
        read_list, _, _ = select.select(sockets, [], [])
        for sock in read_list:
            if sock is server_sock:
                conn, addr = server_sock.accept()
                conn.setblocking(False)
                sockets.append(conn)
            else:
                try:
                    data = sock.recv(1024).decode()
                    if data:
                        response = process_request(data, word_list)
                        sock.sendall(response.encode())
                    else:
                        sockets.remove(sock)
                        sock.close()
                except Exception:
                    sockets.remove(sock)
                    sock.close()

if __name__ == "__main__":
    main()
