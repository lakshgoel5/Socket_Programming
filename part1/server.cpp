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

    string json_str{istreambuf_iterator<char>(file), istreambuf_iterator<char>()};
    //string(begin iterator, end iterator)

    size_t pos = 0; //find returns size_type, so used size_t
    while (true) {
        //extract key
        size_t key_start = json_str.find('"', pos);
        if (key_start == string::npos) break;
        size_t key_end = json_str.find('"', key_start + 1);
        string key = json_str.substr(key_start + 1, key_end - key_start - 1);

        //trim keys
        size_t key_start_trim = key.find_first_not_of(" \t\n\r");
        size_t key_end_trim = key.find_last_not_of(" \t\n\r");
        key = key.substr(key_start_trim, key_end_trim - key_start_trim + 1);

        // find colon after the key
        size_t colon_pos = json_str.find(':', key_end);

        //extract value
        size_t value_start = json_str.find_first_not_of(" \t\n\r", colon_pos + 1);
        size_t value_end = json_str.find_first_of(",}", value_start);

        
        string value = json_str.substr(value_start, value_end - value_start);
        // Trim leading/trailing whitespace and quotes
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
    if (listen(sock, 10) < 0) {
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
    if (client_fd < 0) {
        cerr << "Accept failed\n";
        return 1;
    }

    while (true) {
        char bufferarray[1024] = {0};
        int bytes_read = read(client_fd, bufferarray, sizeof(bufferarray) - 1);
        bufferarray[bytes_read] = '\0';
        string buffer(bufferarray);

        if (bytes_read<=0) {
            cerr << "Error: Could not read p and k" << endl;
            return 0;
        }
        
        //get p,k
        int p, k;
        if (!buffer.empty() && buffer.back() == '\n') {
            buffer.pop_back();
        }
        size_t comma_pos = buffer.find(',');
        if (comma_pos == std::string::npos) {
            return 0; // invalid format
        }
        p = stoi(buffer.substr(0, comma_pos));
        k = stoi(buffer.substr(comma_pos+1));

        buffer.clear();
        int pos = p;
        int n = word_list.size();
        for (pos = p ; pos<p+k && pos<n ; pos++) {
            buffer += word_list[pos];
            buffer += ",";
        }

        if (n<p+k) {
            buffer += "EOF\n";
        }
        else{
            buffer[buffer.size()-1] = '\n'; //replace last comma with newline
        }

        write(client_fd, buffer.c_str(), buffer.size());
    }
    close(client_fd);
    close(sock); //close the socket as we are done with it


    cout << "Server listening on port " << server_port << endl;
}