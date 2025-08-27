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

