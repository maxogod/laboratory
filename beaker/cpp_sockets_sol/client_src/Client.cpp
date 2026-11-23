#include "Client.h"

#include <iostream>
#include <sstream>
#include <string>

// Constructor
Client::Client(const std::string& host, const std::string& port): sv_host(host), sv_port(port) {}

int Client::start_client() {
    this->connect_to_server();

    std::string player_input;
    while (this->protocol.is_player_connected() && getline(std::cin, player_input)) {
        player_input = this->process_input(player_input);
        int err = this->protocol.send_player_action(player_input);
        if (err) {
            return EXIT_FAILURE;
        }
        std::string response = this->protocol.get_server_response();
        if (response == CONNECTION_TERMINATED) {
            break;
        }
        std::cout << response << std::endl;
        player_input.clear();
    }
    return EXIT_SUCCESS;
}

std::string Client::process_input(const std::string& input) const {
    std::string processed_input;
    std::istringstream iss(input);
    std::string word;
    // Remove duplicate spaces
    while (iss >> word) {
        processed_input += word;
        if (!iss.eof()) {
            processed_input += " ";
        }
    }
    return processed_input;
}

void Client::connect_to_server() { this->protocol = Protocol(sv_host, sv_port); }

// Destructor
Client::~Client() = default;
