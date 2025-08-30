CXX = g++
CXXFLAGS = -std=c++17 -Wall #Show all warnings

SERVER_SRC = server.cpp
CLIENT_SRC = client.cpp
#Compilation separated from linking
#If you change a file, then only that file will be recompiled
SERVER_OBJ = $(SERVER_SRC:.cpp=.o)
CLIENT_OBJ = $(CLIENT_SRC:.cpp=.o)

#Compilation
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

all: build
build: server client

#Linking
server: $(SERVER_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

client: $(CLIENT_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

# $! holds the PID of the last background command
# sleep 1 to prevent race conditions
# ------server not killed------
run: build
	@echo "Running server in background..."
	./server &
	PID=$$!
	sleep 1
	@echo "Running client with P=$(P), K=$(K)..."
	P=$(P) K=$(K) ./client
	kill $$PID