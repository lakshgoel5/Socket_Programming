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

void analyse(char *buffer, map<string, int>& freq) {
    while(*buffer != '\0'){
        string key;
        while(*buffer != ','){
            key += *buffer;
            buffer++;
        }
        buffer++; //skip comma
        if(key!="EOF"){
            freq[key]++;
        }
    }
}

void print(map<string, int>& freq) {
    // Print frequency analysis results
    for (const auto& pair : freq) {
        cout << pair.first << ", " << pair.second << endl;
    }
}

int main(int argc, char* argv[]) {
    // get server configuration
    string filename = "config.json";
    string override_k = "";
    string override_p = "";
    bool quiet = true;

    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--config" && i + 1 < argc) {
            filename = argv[++i];
        } else if (arg == "--k" && i + 1 < argc) {
            override_k = argv[++i];
        } else if (arg == "--p" && i + 1 < argc) {
            override_p = argv[++i];
        } else if(arg == "--quiet"){
            quiet = false;
        }
    }
    
    map<string, string> config;
    try{
        config = parse_config(filename);
    } catch (const exception& e) {
        cerr << "Error: Could not parse " << filename << ": " << e.what() << endl;
        return 1;
    }

    //override k and p if provided in command line
    if (!override_k.empty()) config["k"] = override_k;
    if (!override_p.empty()) config["p"] = override_p;

    // connect to server
    const string server_ip = config["server_ip"];
    const int server_port = stoi(config["server_port"]);

    //network connection endpoint
    int sock = socket(AF_INET, SOCK_STREAM, 0); //ipv4, tcp
    if(sock == -1){
        cerr << "Error: Could not create socket" << endl;
        return 1;
    }

    //create server address structure
    struct sockaddr_in serv_addr; //sockaddr_in is specefic version for IPv4 of general sockaddr structure
    serv_addr.sin_family = AF_INET; //ipv4
    //Network protocol: Big-endian (most significant byte first)
    serv_addr.sin_port = htons(server_port); //convert to network byte order

    if (inet_pton(AF_INET, server_ip.c_str(), &serv_addr.sin_addr) <= 0) { //Internet presentation to numeric, converts human readble IP to binary form
        //IPv4, string form in null terminated C style, binary form
        // 1->success, 0->invalid address, -1->error
        cerr << "Invalid address / Address not supported" << endl;
        return 1;
    }

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {  //I want to connect to server whose ip and port is known
        //socket descriptor, server address structure(type cast to generic type)(C style cast recommended), size of the structure
        //Does a three-way handshake SYN ->, SYN-ACK <-, ACK ->
        //returns 0 on success, -1 on error
        cerr << "Connection Failed" << endl;
        return 1;
    }
    cout << "Connected to server " << server_ip << " on port " << server_port << endl;

    //send and receive data
    string k = config["k"];
    string p = config["p"];
    const string message = k + "," + p + "\n"; //message to be sent
    send(sock, message.c_str(), message.length(), 0); //socket descriptor, message in C style, length of the message, flags(0 for no special options)
    cout << "Message sent: " << message << endl;

    //recv takes a charecter array as buffer
    char buffer[1024] = {0}; //1KB buffer for incoming data
    int bytes = recv(sock, buffer, sizeof(buffer)-1, 0); //receive data from server

    close(sock);

    if(bytes > 0){
        buffer[bytes] = '\0'; //null terminate the received string
        cout << "Message received: " << buffer << endl;
        map<string, int> freq;
        analyse(buffer, freq);
        if(quiet==true){
            print(freq);
        }
    }

    return 0;
}
