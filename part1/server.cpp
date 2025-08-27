#include <map>
#include <algorithm>
#include <iostream>
#include <fstream>
#include <string>
#include <sys/socket.h> //core socket API declarations
#include <arpa/inet.h> //address conversion functions
#include <unistd.h> //low-level system call interface
#include <cstring> //string manipulation functions

using namespace std;

map<string, string> parse_config(const string filename){
    map<string, string> config;
    // read the file
    ifstream file(filename); //creates instance and opens the file
    // debug
    if (!file.is_open()) {
        cerr << "Could not open the file '" << filename << "'" << endl;
        return config;
    }

    string line;
    while (getline(file, line)) { //delimiter is newline by default
        //itreate the line
        size_t pos = line.find(':');
        if(pos != string::npos){
            string key = line.substr(0, pos); //pos i.e. ':' not included
            string value = line.substr(pos + 1);

            //trim starting and trailing whitespaces and trailing commas
            key.erase(0, key.find_first_not_of(" "));
            key.erase(key.find_last_not_of(" ,") + 1);
            value.erase(0, value.find_first_not_of(" "));
            value.erase(value.find_last_not_of(" ,") + 1);

            //trim quotes if exist
            if (!key.empty() && key.front() == '"' && key.back() == '"') {
                key = key.substr(1, key.length() - 2);
            }
            if (!value.empty() && value.front() == '"' && value.back() == '"') {
                value = value.substr(1, value.length() - 2);
            }
            config[key] = value;
        }
    }
    return config;
}

int main(){

    string filename = "config.json";
    map<string, string> config;
    try{
        config = parse_config(filename);
    } catch (const exception& e) {
        cerr << "Error: Could not parse " << filename << ": " << e.what() << endl;
        return 1;
    }

    // connect to server
    const string server_ip = config["server_ip"];
    const int server_port = stoi(config["server_port"]);

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if(sock == -1){
        cerr << "Error: Could not create socket" << endl;
        return 1;
    }

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY; //bind to all available interfaces
    addr.sin_port = htons(server_port); //port number

    if (bind(sock, (struct sockaddr*)&addr, (socklen_t)sizeof(addr)) < 0) {
        //socket, address, size of address
        //0->success, -1->failure
        cerr << "Bind failed\n";
        return 1;
    }

    if (listen(sock, 1) < 0) {
        //socket, backlog(max num of pending connections that can be queued)
        //in our case, we will handle one connection at a time
        //0->success, -1->failure
        cerr << "Listen failed\n";
        return 1;
    }

    int client_fd = accept(sock, nullptr, nullptr); //client file descriptor

    //process data

    close(sock); //close the socket as we are done with it

    cout << "Server listening on port " << server_port << endl;
}