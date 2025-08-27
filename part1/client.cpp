#include <map>
#include <algorithm>
#include <iostream>
#include <fstream>
#include <string>

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
            string key = line.substr(0, pos); //pos not included
            string value = line.substr(pos + 2); //+2 to skip ": "
            config[key] = value;            
        }
    }
    return config;
}

