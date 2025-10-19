<div align="center">

  <h1 align="center">Socket Programming</h1>
  <p align="center">
    In networks, sockets are the abstractions available to the application developer. Using socket programming, we implement a basic client-server program along with a few scheduling algorithms
  </p>

</div>

### Authors
- Laksh Goel (2023CS10848)
- Adit Jindal (2023CS50353)

---

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
  - [Part 1: TCP Socket Programming](#part-1-tcp-socket-programming)
  - [Part 2: Concurrent Word Counting Clients](#part-2-concurrent-word-counting-clients)
  - [Part 3: When a Client Gets Greedy (FCFS)](#part-3-when-a-client-gets-greedy-fcfs)
  - [Part 4: When the Server Enforces Fairness (Round Robin)](#part-4-when-the-server-enforces-fairness-round-robin)
- [Part Explanations and Results](#part-explanations-and-results)
  - [Part 1: Word Counting Client](#part-1-word-counting-client)
  - [Part 2: Concurrent Client Handling](#part-2-concurrent-client-handling)
  - [Part 3: FCFS Scheduling with Greedy Client](#part-3-fcfs-scheduling-with-greedy-client)
  - [Part 4: Round-Robin Scheduling](#part-4-round-robin-scheduling)

---

## Overview

This project implements a word counting application using TCP socket programming and explores various scheduling algorithms in a client-server architecture. The assignment is divided into four parts:

1. **Part 1**: Basic TCP socket programming in C++ with a single client-server model
2. **Part 2**: Concurrent client handling using Python with multiple clients
3. **Part 3**: Analysis of FCFS (First-Come-First-Serve) scheduling with greedy clients
4. **Part 4**: Implementation of Round-Robin scheduling for fairness

The project uses **Mininet**, a lightweight network emulator, to test and analyze the performance of different configurations and scheduling algorithms.

---

## Requirements

### System Requirements
- Ubuntu/Linux operating system
- Root/sudo access (required for Mininet)
- Python 3.x
- C++ compiler (g++)
- Make

### Software Dependencies
```bash
# Mininet
sudo apt-get install mininet

# Python packages
pip3 install matplotlib numpy pandas scipy

# C++ compiler
sudo apt-get install g++ make

# Additional utilities
sudo apt-get install poppler-utils  # For PDF processing (if needed)
```

### Hardware Requirements
- Minimum 2GB RAM
- At least 1GB free disk space

---

## Installation and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lakshgoel5/Socket_Programming.git
   cd Socket_Programming
   ```

2. **Install dependencies**:
   ```bash
   # Install Mininet
   sudo apt-get update
   sudo apt-get install mininet
   
   # Install Python dependencies
   pip3 install matplotlib numpy pandas scipy
   ```

3. **Verify Mininet installation**:
   ```bash
   sudo mn --test pingall
   ```

4. **Clean any previous Mininet state**:
   ```bash
   sudo mn -c
   ```

---

## Project Structure

```
Socket_Programming/
├── Assignment2_Complete.pdf      # Complete assignment specification
├── Assignment2_Part1.pdf         # Part 1 specific details
├── report.pdf                    # Project report with results
├── words1.txt                    # Sample word file 1
├── words2.txt                    # Sample word file 2
│
├── part1/                        # Part 1: Basic TCP Socket Programming (C++)
│   ├── server.cpp                # Server implementation in C++
│   ├── client.cpp                # Client implementation in C++
│   ├── Makefile                  # Build and run commands
│   ├── config.json               # Configuration parameters
│   ├── words.txt                 # Word file for counting
│   ├── topo_wordcount.py         # Mininet topology
│   ├── demo_runner.py            # Demo runner script
│   ├── run_experiments.py        # Experiment runner
│   ├── plot_results.py           # Plotting script
│   ├── results.csv               # Experimental results
│   └── p1_plot.png               # Generated plot
│
├── part2/                        # Part 2: Concurrent Clients (Python)
│   ├── server.py                 # Concurrent server using select()
│   ├── client.py                 # Client implementation in Python
│   ├── Makefile                  # Build and run commands
│   ├── config.json               # Configuration parameters
│   ├── words.txt                 # Word file for counting
│   ├── topo_wordcount.py         # Mininet topology
│   ├── runner.py                 # Runner script
│   ├── run_experiments.py        # Experiment runner
│   ├── plot_part2.py             # Plotting script
│   ├── results_part2.csv         # Experimental results
│   └── p2_plot.png               # Generated plot
│
├── part3/                        # Part 3: FCFS with Greedy Client
│   ├── server.py                 # FCFS scheduling server
│   ├── client.py                 # Client with greedy option
│   ├── Makefile                  # Build and run commands
│   ├── config.json               # Configuration parameters
│   ├── words.txt                 # Word file for counting
│   ├── topo_wordcount.py         # Mininet topology
│   ├── runner.py                 # Runner script
│   ├── run_experiments.py        # Experiment runner
│   ├── plot_results.py           # Plotting script (JFI analysis)
│   ├── results.csv               # Experimental results
│   └── p3_plot.png               # Generated plot (JFI vs c)
│
└── part4/                        # Part 4: Round-Robin Scheduling
    ├── server.py                 # Round-Robin scheduling server
    ├── client.py                 # Client implementation
    ├── Makefile                  # Build and run commands
    ├── config.json               # Configuration parameters
    ├── words.txt                 # Word file for counting
    ├── topo_wordcount.py         # Mininet topology
    ├── runner.py                 # Runner script
    ├── run_experiments.py        # Experiment runner
    ├── plot_results.py           # Plotting script (JFI analysis)
    ├── results.csv               # Experimental results
    ├── results_runner.csv        # Additional results
    └── p4_plot.png               # Generated plot (JFI vs c)
```

---

## How to Run

### Part 1: TCP Socket Programming

**Navigate to part1 directory**:
```bash
cd part1
```

**Build the project**:
```bash
make build
```
This compiles `server.cpp` and `client.cpp` into executables.

**Run a single iteration**:
```bash
make run
```
This starts the server and client on Mininet for a single test run.

**Run experiments and generate plots**:
```bash
make plot
```
This runs experiments with varying values of k (1, 2, 5, 10, 20, 50, 100), repeats each 5 times, and generates `p1_plot.png` showing completion time vs k.

**Clean build artifacts**:
```bash
make clean
```

**Manual execution** (without Makefile):
```bash
# Build
g++ -std=c++17 -Wall -c server.cpp -o server.o
g++ -std=c++17 -Wall -o server server.o
g++ -std=c++17 -Wall -c client.cpp -o client.o
g++ -std=c++17 -Wall -o client client.o

# Run with Mininet
sudo mn -c
sudo python3 demo_runner.py
```

### Part 2: Concurrent Word Counting Clients

**Navigate to part2 directory**:
```bash
cd part2
```

**Run a single experiment**:
```bash
make run
```
This starts one server and multiple clients (as specified in `config.json`) on Mininet.

**Run experiments and generate plots**:
```bash
make plot
```
This runs experiments with varying numbers of concurrent clients (1, 5, 9, 13, 17, 21, 25, 29, 32), repeats each configuration, and generates `p2_plot.png` showing average completion time per client vs number of clients.

**Clean results**:
```bash
make clean
```

**Manual execution**:
```bash
sudo mn -c
sudo python3 runner.py
```

### Part 3: When a Client Gets Greedy (FCFS)

**Navigate to part3 directory**:
```bash
cd part3
```

**Run FCFS experiment**:
```bash
make run-fcfs
```
This runs one experiment with FCFS scheduling using parameters from `config.json`.

**Run experiments and generate plots**:
```bash
make plot
```
This runs experiments with varying values of c (the number of parallel requests from greedy client: 1, 11, 21, 31, 41, 51, 61, 71, 81) and generates `p3_plot.png` showing Jain's Fairness Index (JFI) vs c.

**Clean results**:
```bash
make clean
```

### Part 4: When the Server Enforces Fairness (Round Robin)

**Navigate to part4 directory**:
```bash
cd part4
```

**Run Round-Robin experiment**:
```bash
make run-rr
```
This runs one experiment with Round-Robin scheduling using parameters from `config.json`.

**Run experiments and generate plots**:
```bash
make plot
```
This runs experiments with varying values of c and generates `p4_plot.png` showing Jain's Fairness Index (JFI) vs c under Round-Robin scheduling.

**Clean results**:
```bash
make clean
```

---

## Part Explanations and Results

### Part 1: Word Counting Client

#### Explanation
Part 1 implements a basic client-server word counting application using TCP sockets in C++. The protocol works as follows:

1. **Server**: 
   - Listens on a predefined IP (10.0.0.2) and port (5000)
   - Maintains a file `words.txt` with comma-separated words
   - Responds to client requests with word chunks

2. **Client**:
   - Connects to the server via TCP
   - Sends requests in format `p,k\n` where:
     - `p` = starting offset (zero-indexed)
     - `k` = number of words to fetch
   - Receives words from server
   - Counts word frequencies
   - Prints results

3. **Protocol**:
   - Client requests: `p,k\n`
   - Server responses: `word1,word2,...,wordN\n` or includes `EOF` when end of file reached

#### Experiment
The experiment varies k (number of words per request) with values: 1, 2, 5, 10, 20, 50, 100. Each configuration is run 5 times to compute average completion time and 95% confidence intervals.

#### Results
Based on the data in `part1/results.csv`:

- **k=1**: Average ~36.4ms (highest latency due to many round trips)
- **k=2**: Average ~19.4ms
- **k=5**: Average ~7.4ms
- **k=10**: Average ~4.6ms
- **k=20**: Average ~5.0ms
- **k=50**: Average ~3.2ms
- **k=100**: Average ~1.2ms (lowest latency)

**Observations**:
- Completion time **decreases** as k increases
- Fewer network round trips with larger k values lead to better performance
- Network latency dominates when k is small (many requests needed)
- Diminishing returns as k grows beyond 50
- Trade-off between request size and number of requests

The plot `p1_plot.png` visualizes this relationship with confidence intervals.

---

### Part 2: Concurrent Client Handling

#### Explanation
Part 2 extends the server to handle multiple concurrent client connections using Python's `select()` module:

1. **Server**:
   - Uses non-blocking sockets with `select.select()`
   - Maintains multiple active connections simultaneously
   - Processes requests in First-Come-First-Serve (FCFS) order
   - Queues pending requests when busy

2. **Client**:
   - Multiple clients connect concurrently
   - Each downloads the complete word file
   - Records individual completion time

3. **Network Topology**:
   - 2 hosts (h1 for clients, h2 for server)
   - Connected via switch with 100 Mbps bandwidth

#### Experiment
The experiment varies the number of concurrent clients from 1 to 32 (incremented by 4). Each configuration is run multiple times to measure average completion time per client.

#### Results
Based on the data in `part2/results_part2.csv`:

- **1 client**: Average ~24.9ms
- **5 clients**: Average ~101.2ms
- **9 clients**: Average ~165.4ms
- **13 clients**: Average ~264.3ms
- **17 clients**: Average ~351.9ms
- **21 clients**: Average ~456.7ms
- **25 clients**: Average ~535.3ms
- **29 clients**: Average ~638.2ms
- **32 clients**: Average ~654.8ms

**Observations**:
- Completion time per client **increases linearly** with number of clients
- Server processes requests sequentially (FCFS), causing queueing delays
- With n clients, average wait time increases proportionally
- Linear scaling indicates CPU-bound processing (not network-bound)
- No parallelism in request processing

The plot `p2_plot.png` shows this linear relationship with confidence intervals.

---

### Part 3: FCFS Scheduling with Greedy Client

#### Explanation
Part 3 analyzes fairness issues with FCFS scheduling when a "greedy" client sends multiple requests back-to-back:

1. **Setup**:
   - 10 clients total
   - 1 greedy client sends `c` requests immediately (without waiting for responses)
   - 9 normal clients send requests one-at-a-time
   - All clients request k=5 words per request

2. **Greedy Behavior**:
   - Greedy client sends c requests back-to-back
   - Occupies c positions in the server's request queue
   - Normal clients get squeezed between greedy client's requests

3. **Fairness Metric**:
   - **Jain's Fairness Index (JFI)**: 
     ```
     JFI = (Σxi)² / (n * Σxi²)
     ```
     where xi is completion time for client i
   - JFI ranges from 1/n (worst) to 1.0 (best/perfect fairness)
   - JFI close to 1.0 means all clients finish around the same time

#### Experiment
Vary c (number of parallel requests from greedy client) from 1 to 81 (incremented by 10). Measure completion times and compute JFI.

#### Results
Based on the data in `part3/results.csv`:

- **c=1**: JFI ≈ 0.996 (nearly perfect fairness)
- **c=11**: JFI ≈ 0.982 (slight unfairness)
- **c=21**: JFI ≈ 0.878 (moderate unfairness)
- **c=31**: JFI ≈ 0.655 (significant unfairness)
- **c=41**: JFI ≈ 0.584
- **c=51**: JFI ≈ 0.462
- **c=61**: JFI ≈ 0.366
- **c=71**: JFI ≈ 0.371
- **c=81**: JFI ≈ 0.182 (severe unfairness)

**Observations**:
- **Fairness degrades significantly** as c increases
- Greedy client monopolizes server by occupying queue positions
- Normal clients face long wait times
- FCFS cannot prevent greedy behavior
- At high c values, greedy client completes much faster than others
- System becomes highly unfair (JFI drops below 0.2)

**Implications**:
- FCFS is vulnerable to greedy clients
- No mechanism to enforce fairness
- If c increased further, one client could completely starve others

The plot `p3_plot.png` shows JFI decreasing as c increases.

---

### Part 4: Round-Robin Scheduling

#### Explanation
Part 4 implements Round-Robin (RR) scheduling to address fairness issues:

1. **Round-Robin Policy**:
   - Server maintains a queue of client connections
   - Cycles through clients in fixed order
   - Serves **one request** from each client before moving to next
   - Prevents any single client from monopolizing the server

2. **Implementation**:
   - Server uses `collections.deque` to maintain per-client request queues
   - Tracks current position with `rr_idx`
   - Serves one request from client at `rr_idx`, then increments
   - Wraps around to beginning when reaching end of client list

3. **Expected Behavior**:
   - Even if greedy client sends many requests, they're interleaved with others
   - All clients get fair share of server time
   - Completion times should be more uniform

#### Experiment
Same setup as Part 3: 10 clients (1 greedy with c parallel requests, 9 normal). Vary c and measure JFI.

#### Results
Based on the data in `part4/results_runner.csv`:

- **c=50 (Run 1)**: JFI ≈ 0.998 (excellent fairness)
- **c=50 (Run 2)**: JFI ≈ 0.962 (very good fairness)

**Comparison with FCFS** (at c=51):
- **FCFS**: JFI ≈ 0.462
- **Round-Robin**: JFI ≈ 0.980

**Observations**:
- **Round-Robin maintains high fairness** even with greedy clients
- JFI stays close to 1.0 across different c values
- Greedy client cannot monopolize server
- All clients get fair turn regardless of request patterns
- Much more robust against greedy behavior than FCFS

**Limitations**:
- A client could still send extremely large values of c
- But the impact is limited since requests are interleaved
- Server resources (memory for queuing) could become a bottleneck
- With very high c, the greedy client's queue grows but doesn't block others

The plot `p4_plot.png` shows JFI remaining high (near 1.0) as c increases under Round-Robin scheduling.

---

### Summary Comparison

| Scheduling Algorithm | Fairness (JFI at c=50) | Vulnerability to Greedy Clients | Complexity |
|---------------------|------------------------|--------------------------------|------------|
| **FCFS** (Part 3)   | ~0.46 (Poor)          | High - easily monopolized      | Low        |
| **Round-Robin** (Part 4) | ~0.98 (Excellent) | Low - inherently fair         | Medium     |

**Key Takeaway**: Round-Robin scheduling provides significantly better fairness than FCFS when dealing with greedy clients, at the cost of slightly more complex implementation.

---

## Notes

This project was completed as Assignment 2 for the course **COL334/672: Computer Networks** (Diwali'25 semester).

**Full Problem Statement**: See `Assignment2_Complete.pdf` for detailed specifications.

**Project Report**: See `report.pdf` for comprehensive analysis and results.

1. **Mininet Requirements**: All experiments require sudo/root access to run Mininet
2. **Network Cleanup**: Always run `sudo mn -c` before experiments to clean previous state
3. **Results**: Experimental results are stored in CSV files and plots are generated as PNG images
4. **Configuration**: Each part has a `config.json` file with tunable parameters
5. **Word Files**: Sample word files (`words.txt`, `words1.txt`, `words2.txt`) are provided

