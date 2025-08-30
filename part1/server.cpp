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

int main(){

    // load config
    string filename = "config.json";
    string words = "words.txt";
    map<string, string> config;
    try{
        config = parse_config(filename);
    } catch (const exception& e) {
        cerr << "Error: Could not parse " << filename << ": " << e.what() << endl;
        return 1;
    }

    // load words
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

    struct sockaddr_in addr;
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

    //process data


    close(sock); //close the socket as we are done with it

    cout << "Server listening on port " << server_port << endl;
}