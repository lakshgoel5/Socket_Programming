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

map<string, string> parse_config(const string& filename) {
    map<string, string> config;
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Could not open the file '" << filename << "'" << endl;
        return config;
    }
    
    // Read entire file as a single string
    string json_str((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    
    size_t pos = 0;
    while (true) {
        // Find next key opening quote
        size_t key_start = json_str.find('"', pos);
        if (key_start == string::npos) break;
        
        size_t key_end = json_str.find('"', key_start + 1);
        if (key_end == string::npos) break;
        
        string key = json_str.substr(key_start + 1, key_end - key_start - 1);
        
        // Find colon after the key
        size_t colon_pos = json_str.find(':', key_end);
        if (colon_pos == string::npos) break;
        
        // Find value start (skip whitespace)
        size_t value_start = json_str.find_first_not_of(" \t\n\r", colon_pos + 1);
        if (value_start == string::npos) break;
        
        string value;
        if (json_str[value_start] == '"') {
            // Value is a string, find closing quote
            size_t value_end = json_str.find('"', value_start + 1);
            if (value_end == string::npos) break;
            value = json_str.substr(value_start + 1, value_end - value_start - 1);
            pos = value_end + 1;
        } else {
            // Value is number or boolean; find comma or end brace
            size_t value_end = json_str.find_first_of(",}", value_start);
            if (value_end == string::npos) break;
            value = json_str.substr(value_start, value_end - value_start);
            pos = value_end + 1;
            // Trim whitespace from value ends
            size_t val_start_trim = value.find_first_not_of(" \t\n\r");
            size_t val_end_trim = value.find_last_not_of(" \t\n\r");
            value = value.substr(val_start_trim, val_end_trim - val_start_trim + 1);
        }
        
        config[key] = value;
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
    // cout << "Connected to server " << server_ip << " on port " << server_port << endl;

    //send and receive data
    string k = config["k"];
    string p = config["p"];
    const string message = k + "," + p + "\n"; //message to be sent
    send(sock, message.c_str(), message.length(), 0); //socket descriptor, message in C style, length of the message, flags(0 for no special options)
    // cout << "Message sent: " << message << endl;

    //recv takes a charecter array as buffer
    char buffer[1024] = {0}; //1KB buffer for incoming data
    int bytes = recv(sock, buffer, sizeof(buffer)-1, 0); //receive data from server

    close(sock);

    if(bytes > 0){
        buffer[bytes] = '\0'; //null terminate the received string
        // cout << "Message received: " << buffer << endl;
        map<string, int> freq;
        analyse(buffer, freq);
        if(quiet==true){
            print(freq);
        }
    }

    return 0;
}
