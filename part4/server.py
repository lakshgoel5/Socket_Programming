#!/usr/bin/env python3
import socket
import select
import json
import traceback
from collections import deque

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

def process_request(line, word_list):
    line = line.strip()
    if not line:
        return "EOF\n"
    try:
        p_str, k_str = line.split(",")
        p, k = int(p_str), int(k_str)
    except Exception:
        return "EOF\n"

    n = len(word_list)
    if p >= n:
        return "EOF\n"

    end = min(p + k, n)
    response_words = word_list[p:end]
    if end >= n:
        response_words = response_words + ["EOF"]
    return ",".join(response_words) + "\n"

def main():
    cfg = load_config()
    words = load_words(cfg.get("filename", "words.txt"))
    server_ip = cfg["server_ip"]
    server_port = int(cfg["server_port"])

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((server_ip, server_port))
    srv.listen(32)
    srv.setblocking(False)

    print(f"[srv] RR server listening on {server_ip}:{server_port}")

    clients = []          # sockets in accept order => RR order
    addrs = {}            # sock -> addr
    recv_buf = {}         # sock -> partial receive buffer (string)
    pending = {}          # sock -> deque of parsed request lines
    rr_idx = 0            # index into clients for next RR turn
    sockets = [srv] #List of all Sockets


    try:
        while True:
            try:
                read_list, _, _ = select.select(sockets, [], [], 0.5)
            except Exception:
                continue

            # First: handle reads -> accumulate parsed lines into pending queues
            for s in read_list:
                if s is srv:
                    # accept new connection
                    try:
                        conn, addr = srv.accept()
                        conn.setblocking(False)
                        clients.append(conn)
                        addrs[conn] = addr
                        recv_buf[conn] = ""
                        pending[conn] = deque()
                        print(f"[srv] accepted {addr}")
                    except Exception as e:
                        print("[srv] accept error:", e)
                    continue

                # client socket has data
                try:
                    data = s.recv(4096)
                except Exception:
                    addr = addrs.get(s, "<unknown>")
                    print(f"[srv] recv error, closing {addr}")
                    if s in clients: clients.remove(s)
                    recv_buf.pop(s, None)
                    pending.pop(s, None)
                    addrs.pop(s, None)
                    try: s.close()
                    except: pass
                    # adjust rr_idx if needed
                    if rr_idx >= len(clients): rr_idx = 0
                    continue

                if not data:
                    # client closed
                    addr = addrs.get(s, "<unknown>")
                    # print(f"[srv] client {addr} closed")
                    if s in clients: clients.remove(s)
                    recv_buf.pop(s, None)
                    pending.pop(s, None)
                    addrs.pop(s, None)
                    try: s.close()
                    except: pass
                    if rr_idx >= len(clients): rr_idx = 0
                    continue

                # decode and split complete lines, enqueue them
                chunk = data.decode('utf-8', errors='replace')
                buf = recv_buf.get(s, "") + chunk
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    line = line.strip()
                    if line == "":
                        continue
                    pending.setdefault(s, deque()).append(line)
                    # debug: print enqueued request
                    # print(f"[srv] enqueued {addrs.get(s)}: {repr(line)}")
                recv_buf[s] = buf

            # Second: scheduling step (one request per client per round-robin turn)
            # If no clients or no pending anywhere, skip
            if not clients:
                continue
            if not any(pending.get(c) and len(pending[c])>0 for c in clients):
                continue

            # Start scanning from rr_idx and find the next client that has pending requests.
            # Serve only one request from that client, then advance rr_idx to the next client.
            start = rr_idx % len(clients)
            tried = 0
            idx = start
            served = False
            while tried < len(clients):
                c = clients[idx]
                q = pending.get(c)
                if q and len(q) > 0:
                    req = q.popleft()
                    addr = addrs.get(c, "<unknown>")
                    try:
                        resp = process_request(req, words)
                    except Exception:
                        resp = "EOF\n"
                    # send response
                    try:
                        # print(f"[srv-debug] serving {addr} req={repr(req)} -> resp={repr(resp.strip())}")
                        c.sendall(resp.encode('utf-8'))
                    except Exception:
                        # send failed; close client
                        print(f"[srv] send error to {addr}, closing")
                        if c in clients: clients.remove(c)
                        recv_buf.pop(c, None)
                        pending.pop(c, None)
                        addrs.pop(c, None)
                        if rr_idx >= len(clients): rr_idx = 0
                        served = True
                        break

                    # optionally print served mapping for debugging
                    print(f"[srv] served {addr} req={req} -> {resp.strip()}")

                    # If response contained EOF, close client so client sees EOF and exits
                    if "EOF" in resp:
                        print(f"[srv] closing {addr} after EOF")
                        if c in clients: clients.remove(c)
                        recv_buf.pop(c, None)
                        pending.pop(c, None)
                        addrs.pop(c, None)
                        # adjust rr_idx to valid range
                        if rr_idx >= len(clients): rr_idx = 0
                    else:
                        # advance rr pointer to next client after this one
                        if clients:
                            rr_idx = (idx + 1) % len(clients)
                    served = True
                    break
                # advance to next client in list
                idx = (idx + 1) % len(clients)
                tried += 1

            # If we scanned all clients and none had pending, nothing to do this loop
            # (We re-enter select and wait for more data)
            # If we served one, we go back to select for fairness and responsiveness.

    except KeyboardInterrupt:
        print("[srv] exiting on KeyboardInterrupt")
    except Exception:
        print("[srv] unexpected error")
        traceback.print_exc()
    finally:
        for c in list(clients):
            try: c.close()
            except: pass
        try: srv.close()
        except: pass
        print("[srv] server terminated")

if __name__ == "__main__":
    main()
