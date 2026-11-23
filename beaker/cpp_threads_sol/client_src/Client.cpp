#include "Client.h"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// Constructor
Client::Client(const std::string& host, const std::string& port): protocol(host, port) {}

void Client::start_client() {

    while (this->protocol.is_player_connected() && !std::cin.eof()) {
        std::string command = get_command();

        if (command == EXIT_STR) {
            break;
        } else if (command == ATTACK_STR) {
            this->protocol.send_player_attack();
        } else if (command == READ_STR) {
            int amount_of_msg = get_amount_of_msg_to_read();
            std::vector<GameEvent> events = this->protocol.get_server_broadcast(amount_of_msg);
            if (events.empty()) {
                break;  // Connection was terminated by server
            }

            for (const auto& event: events) {
                std::cout << event << std::endl;
            }
        } else {
            std::cout << "Invalid command" << std::endl;
        }
    }
}

int Client::get_amount_of_msg_to_read() {
    std::string input;
    std::cin >> input;
    return std::stoi(input);
}

std::string Client::get_command() {
    std::string input;
    std::cin >> input;

    // make input uppercase
    std::transform(input.begin(), input.end(), input.begin(), ::toupper);

    return input;
}

// Destructor
Client::~Client() = default;
