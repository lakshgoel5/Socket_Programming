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

bool load_words(const string filename, vector<string>& words){
    ifstream file(filename);
    if(!file.is_open()){
        cerr << "Could not open the file '" << filename << "'" << endl;
        return false;
    }

    string line;
    while(getline(file, line)){
        //separate words by comma and push in vector
        size_t start = 0;
        size_t end = line.find(',');
        while(end != string::npos){
            string word = line.substr(start, end - start);
            //trim whitespaces //for handling word1, , word2
            word.erase(0, word.find_first_not_of(" "));
            word.erase(word.find_last_not_of(" ") + 1);
            if(!word.empty()){
                words.push_back(word);
            }
            start = end + 1;
            end = line.find(',', start);
        }
        //last word
        string word = line.substr(start);
        word.erase(0, word.find_first_not_of(" "));
        word.erase(word.find_last_not_of(" ") + 1);
        if(!word.empty()){
            words.push_back(word);
        }
    }
    words.push_back("EOF"); //end of file marker
    return true;
}

void handle_client(int client_fd, const vector<string>& word_list){
    char bufferarray[1024] = {0};
    int bytes_read = read(client_fd, bufferarray, sizeof(bufferarray) - 1);
    bufferarray[bytes_read] = '\0';
    string buffer(bufferarray);

    if (bytes_read<=0) {
        cerr << "Error: Could not read p and k" << endl;
        return;
    }
    
    int p, k;
    if (!buffer.empty() && buffer.back() == '\n') {
        buffer.pop_back();
    }
    size_t comma_pos = buffer.find(',');
    if (comma_pos == std::string::npos) {
        return; // invalid format
    }
    p = stoi(buffer.substr(0, comma_pos));
    k = stoi(buffer.substr(comma_pos+1));

    buffer.clear();
    int start_pos = p;
    int n = word_list.size();
    for ( ; start_pos<p+k && start_pos<n ; start_pos++) {
        buffer += word_list[start_pos];
        buffer += ",";
    }

    if (start_pos<p+k-1) {
        buffer += "EOF\n";
    }

    write(client_fd, buffer.c_str(), buffer.size());
}

int main(int argc, char* argv[]){

    // load config
    string filename = "config.json";
    string words = "words.txt";

    // parse arguments
    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--config" && i + 1 < argc) {
            filename = argv[++i];
        }
        else if (arg == "--words" && i + 1 < argc) {
            words = argv[++i];
        }
    }

    map<string, string> config;
    try{
        config = parse_config(filename);
    } catch (const exception& e) {
        cerr << "Error: Could not parse " << filename << ": " << e.what() << endl;
        return 1;
    }

    // // load words
    vector<string> word_list;
    if(!load_words(words, word_list)){
        cout << "Error: Could not load words from " << words << endl;
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

    //------debug------
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr)); //---debug---
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY; //bind to all available interfaces
    addr.sin_port = htons(server_port); //port number

    //assign a specific address and port to the socket
    if (bind(sock, (struct sockaddr*)&addr, (socklen_t)sizeof(addr)) < 0) {
        //socket, address, size of address
        //0->success, -1->failure
        cerr << "Bind failed\n";
        return 1;
    }

    //passive listening state, ready to accept incoming requests
    if (listen(sock, 1) < 0) {
        //socket, backlog(max num of pending connections that can be queued)
        //in our case, we will handle one connection at a time
        //0->success, -1->failure
        cerr << "Listen failed\n";
        return 1;
    }

    //program waits at this line until a client connects to the server
    int client_fd = accept(sock, nullptr, nullptr); //returns client file descriptor
    //All future communication with this specific client (like send() and recv()) will happen through this new client_fd, 
    //while the original sock goes back to listening for other new clients.

    //We will have just one connection request in the backlog queue ------debug------
    if (client_fd < 0) {
        cerr << "Accept failed\n";
        return 1;
    }

    //-----debug----- check whether sock closed before or after accept
    //process data
    handle_client(client_fd, word_list);
    close(client_fd);
    close(sock); //close the socket as we are done with it


    cout << "Server listening on port " << server_port << endl;
}