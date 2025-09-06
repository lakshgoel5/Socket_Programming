#!/usr/bin/env python3
import socket
import threading
import queue #for making queue
import sys
import json
import time

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
    return words

def processing_worker():
    """
    A single worker thread that processes requests from the queue one by one (FCFS).
    This ensures sequential processing of requests from all concurrent clients.
    """
    print("Processing worker thread started.")
    while True:
        try:
            # Block until a request is available
            client_socket, p, k, client_addr = request_queue.get()

            # --- Request Processing Logic ---
            response_words = []
            eof_reached = False

            if p >= len(word_list):
                eof_reached = True
            else:
                end_index = min(p + k, len(word_list))
                response_words = word_list[p:end_index]
                if end_index == len(word_list):
                    eof_reached = True

            # Format the response string based on the protocol
            if response_words:
                response_str = ",".join(response_words)
                if eof_reached:
                    response_str += ",EOF\n"
                else:
                    response_str += "\n"
            else: # Handles cases where p is out of bounds from the start
                response_str = "EOF\n"
            # --- End Processing Logic ---

            # Send the response back to the correct client
            client_socket.sendall(response_str.encode('utf-8'))

        except Exception as e:
            print(f"Error processing request for {client_addr}: {e}")
        finally:
            # Indicate that the task from the queue is done
            request_queue.task_done()


# Thread-safe queue for FCFS processing. Stores tuples of:
# (client_socket, p_value, k_value, client_address)
request_queue = queue.Queue()
word_list = [] # Global word list, loaded once at startup

def handle_client(client_socket, client_address):
    print(f"Accepted connection from {client_address}")
    buffer = ""
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8') #receive 1024 bytes, decode to string
            if not data:
                break
            buffer += data

            try:
                #Split \n from buffer
                request_line, buffer = buffer.split('\n')
                p_str, k_str = request_line.split(',')
                p = int(p_str)
                k = int(k_str)
                request_queue.put((client_socket, p, k, client_address))
            except (ValueError, IndexError):
                print(f"Invalid request format from {client_address}: '{request_line}'")

    except ConnectionResetError:
        print(f"Connection reset by {client_address}")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        print(f"Closing connection for {client_address}")
        client_socket.close()

def main():
    global word_list #Use the global one instead
    config = parse_config("config.json")
    if not config:
        return 1
    
    server_ip = config.get("server_ip", "0.0.0.0")
    server_port = int(config.get("server_port", 5000))
    num_clients = int(config.get("num_clients", 1))
    filename = config.get("filename", "words.txt")

    try:
        word_list = load_words(filename)
    except FileNotFoundError:
        print(f"FATAL: Word file '{filename}' not found. Exiting.")
        return

    # It's a daemon so it exits when the main thread exits.
    # A thread to process the queue
    worker_thread = threading.Thread(target=processing_worker, daemon=True)
    worker_thread.start()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(num_clients, num_clients+5)
    print(f"Server listening on {server_ip}:{server_port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept() #accept a connection and create a new thread to handle it
            handler_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            handler_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()
    return 0

if __name__ == "__main__":
    main()
