#!/usr/bin/env python3
import socket
import json
import select
import traceback

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

    # create TCP socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((server_ip, server_port))
    server_sock.listen(64)  # backlog
    server_sock.setblocking(False)

    sockets = [server_sock]
    buffers = {}  # per-connection receive buffer: conn -> str
    addrs = {}    # optional mapping conn -> addr for logging

    # print(f"[srv] Concurrent server listening on {server_ip}:{server_port}")

    while True:
        try:
            read_list, _, _ = select.select(sockets, [], [], 1.0)
        except Exception as e:
            # print("[srv] select error:", e)
            continue

        for sock in read_list:
            if sock is server_sock:
                try:
                    conn, addr = server_sock.accept()
                    conn.setblocking(False)
                    sockets.append(conn)
                    buffers[conn] = ""
                    addrs[conn] = addr
                    # print(f"[srv] accepted connection from {addr}")
                except Exception as e:
                    print("[srv] accept error:", e)
                continue

            # handle client socket readable
            try:
                data = sock.recv(4096)
                if not data:
                    # client closed connection
                    addr = addrs.get(sock, "<unknown>")
                    # print(f"[srv] client {addr} closed connection")
                    if sock in sockets:
                        sockets.remove(sock)
                    buffers.pop(sock, None)
                    addrs.pop(sock, None)
                    try:
                        sock.close()
                    except Exception:
                        pass
                    continue

                chunk = data.decode('utf-8', errors='replace')
                addr = addrs.get(sock, "<unknown>")
                # debug print
                # print(f"[srv] recv from {addr}: {repr(chunk)}")

                buf = buffers.get(sock, "") + chunk
                # while we have at least one full request line, process it
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    line = line.strip()
                    if line == "":
                        # ignore empty lines
                        continue
                    response = process_request(line, word_list)
                    # debug print
                    # print(f"[srv] {addr} req={repr(line)} -> resp={repr(response.strip())}")

                    try:
                        sock.sendall(response.encode('utf-8'))
                    except Exception as e:
                        print(f"[srv] send error to {addr}: {e}")
                        # drop connection
                        break

                    # If response contains EOF, close the connection so client can finish
                    if "EOF" in response:
                        print(f"[srv] closing {addr} after EOF")
                        if sock in sockets:
                            sockets.remove(sock)
                        buffers.pop(sock, None)
                        addrs.pop(sock, None)
                        try:
                            sock.close()
                        except Exception:
                            pass
                        # after closing, stop processing this socket
                        buf = ""  # discard any leftover
                        break

                # save leftover partial line, if connection still open
                if sock in sockets:
                    buffers[sock] = buf

            except Exception as e:
                addr = addrs.get(sock, "<unknown>")
                # print(f"[srv] exception for {addr}: {e}")
                traceback.print_exc()
                if sock in sockets:
                    sockets.remove(sock)
                buffers.pop(sock, None)
                addrs.pop(sock, None)
                try:
                    sock.close()
                except Exception:
                    pass


if __name__ == "__main__":
    main()