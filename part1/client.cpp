#include <map>
#include <algorithm>
#include <iostream>
#include <fstream>
#include <string>
#include <sys/socket.h>
#include <arpa/inet.h> 
#include <unistd.h> 
#include <cstring> 
#include <chrono>

using namespace std;

map<string, string> parse_config(const string& filename) {
    map<string, string> config;
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Could not open the file '" << filename << "'" << endl;
        return config;
    }

    string json_str{istreambuf_iterator<char>(file), istreambuf_iterator<char>()};

    size_t pos = 0;
    while (true) {
        size_t key_start = json_str.find('"', pos);
        if (key_start == string::npos) break;
        size_t key_end = json_str.find('"', key_start + 1);
        string key = json_str.substr(key_start + 1, key_end - key_start - 1);

        size_t key_start_trim = key.find_first_not_of(" \t\n\r");
        size_t key_end_trim = key.find_last_not_of(" \t\n\r");
        key = key.substr(key_start_trim, key_end_trim - key_start_trim + 1);

        size_t colon_pos = json_str.find(':', key_end);

        //extract value
        size_t value_start = json_str.find_first_not_of(" \t\n\r", colon_pos + 1);
        size_t value_end = json_str.find_first_of(",}", value_start);

        
        string value = json_str.substr(value_start, value_end - value_start);
        size_t start_trim = value.find_first_not_of(" \t\n\r\"");
        size_t end_trim   = value.find_last_not_of(" \t\n\r\"");
        if (start_trim == string::npos) {
            value = "";
        } else {
            value = value.substr(start_trim, end_trim - start_trim + 1);
        }

        //store in map
        config[key] = value;

        pos = value_end + 1;
    }
    
    return config;
}

void analyse(char *buffer, map<string, int>& freq) {
    while (*buffer != '\0') {
        string key;
        while (*buffer != ',' && *buffer != '\0') {
            key += *buffer;
            buffer++;
        }
        if (*buffer == ',') {
            buffer++; 
        }
        if (!key.empty() && key.back() == '\n') {
            key.pop_back();
        }
        if (key == "EOF") {
            break;
        }
        if (!key.empty()) {
            freq[key]++;
        }
    }
}

void print(map<string, int>& freq) {
    for (auto it = freq.begin(); it != freq.end(); ) {
        cout << it->first << ", " << it->second;
        if (++it != freq.end()) cout << "\n";
    }
}

int main(int argc, char* argv[]) {
    string filename = "config.json";
    string override_k = "";
    string override_p = "";
    bool quiet = false;

    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--config" && i + 1 < argc) {
            filename = argv[++i];
        } else if (arg == "--k" && i + 1 < argc) {
            override_k = argv[++i];
        } else if (arg == "--p" && i + 1 < argc) {
            override_p = argv[++i];
        } else if(arg == "--quiet"){
            quiet = true;
        }
    }
    
    map<string, string> config;
    try {
        config = parse_config(filename);
    } catch (const exception& e) {
        cerr << "Error: Could not parse " << filename << ": " << e.what() << endl;
        return 1;
    }
    //override k and p if in command line
    if (!override_k.empty()) config["k"] = override_k;
    if (!override_p.empty()) config["p"] = override_p;

    const string server_ip = config["server_ip"];
    const int server_port = stoi(config["server_port"]);

    int sock = socket(AF_INET, SOCK_STREAM, 0); //ipv4, tcp
    if(sock == -1){
        cerr << "Error: Could not create socket" << endl;
        return 1;
    }

    struct sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET; //ipv4
    serv_addr.sin_port = htons(server_port); //convert to network byte order

    if (inet_pton(AF_INET, server_ip.c_str(), &serv_addr.sin_addr) <= 0) {
        cerr << "Invalid address / Address not supported" << endl;
        return 1;
    }

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) { 
        cerr << "Connection Failed" << endl;
        return 1;
    }
    // cout << "Connected to server " << server_ip << " on port " << server_port << endl;

    //send and receive data
    string k = config["k"];
    string p = config["p"];
    string message = p + "," + k + "\n";
    int p_int = stoi(p);
    int k_int = stoi(k);

    //starting clock
    auto start = std::chrono::high_resolution_clock::now();
    string all_data;
    int i=0;
    while(true){
        i++;
        send(sock, message.c_str(), message.length(), 0); 
        // cout << "Message sent: " << message << endl;
        int bytes = 0;
        char buffer[1024];
        bytes = recv(sock, buffer, sizeof(buffer)-1, 0);

        //process buffer received
        buffer[bytes-1] = ',';
        buffer[bytes] = '\0';
        all_data.append(buffer);
        if (strstr(buffer, "EOF") != NULL) {
            break;
        }

        //increment p and create new message
        p_int+=k_int;
        // cout << p << endl;
        message = to_string(p_int) + "," + k + "\n";
    }

    //end clock time
    auto end = std::chrono::high_resolution_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    double elapsed_msec = elapsed / 1e3;
    cout << "ELAPSED_MS:" << elapsed_msec << endl;

    close(sock);

    if(!all_data.empty()){
        all_data.pop_back();
        // cout << "Message received: " << all_data << endl;
        map<string, int> freq;
        char* cstr = new char[all_data.size()+1];
        strcpy(cstr, all_data.c_str());
        // cout << cstr << endl;
        analyse(cstr, freq);
        if(quiet==false){
            print(freq);
        }
    }

    return 0;
}
