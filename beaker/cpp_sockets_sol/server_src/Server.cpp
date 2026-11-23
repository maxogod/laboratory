#include "Server.h"

#include <cstring>
#include <functional>
#include <iostream>
#include <queue>
#include <sstream>
#include <unordered_map>
#include <utility>
#include <vector>

// Constructor
Server::Server(const std::string& port): sv_port(port) {}

int Server::start_server() {
    accept_players();
    int amount_of_actions = 0;
    while (this->protocol.is_player_connected()) {
        std::string player_actions = this->protocol.get_player_action();
        if (player_actions == CONNECTION_TERMINATED) {
            break;
        }
        std::string processed_actions = this->process_player_actions(player_actions);
        amount_of_actions += count_processed_actions(processed_actions);
        int err = this->protocol.send_server_response(processed_actions);
        if (err) {
            return EXIT_FAILURE;
        }
    }
    std::cout << "Actions: " << amount_of_actions << std::endl;
    return EXIT_SUCCESS;
}

void Server::accept_players() { this->protocol = Protocol(sv_port); }

std::string Server::process_player_actions(std::string& player_actions) {

    std::priority_queue<std::pair<size_t, size_t>, std::vector<std::pair<size_t, size_t>>,
                        std::greater<>>
            min_queue;

    // Find and enqueue all possible combos
    for (const auto& combo: this->possible_combos) {
        size_t pos = player_actions.find(combo.first);
        while (pos != std::string::npos) {
            min_queue.emplace(pos, combo.first.length());
            pos = player_actions.find(combo.first, pos + combo.first.length());
        }
    }

    // Replace all combos
    int last_end_pos = -1;  // End position of last combo
    int err = 0;            // Error to keep track of the difference in length
    while (!min_queue.empty()) {
        auto top_pair = min_queue.top();
        int pos = top_pair.first - err;  // Adjust for the difference in length
        int len = top_pair.second;

        if (last_end_pos >= pos) {
            min_queue.pop();  // Skip overlapping combos
            continue;
        }
        min_queue.pop();

        std::string combo_replace = possible_combos[player_actions.substr(pos, len)];
        player_actions.replace(pos, len, combo_replace);
        last_end_pos = pos + combo_replace.size();
        err += (len - combo_replace.size());
    }

    return player_actions;
}

int Server::count_processed_actions(const std::string& processed_actions) {
    int amount_of_actions = 0;
    std::istringstream iss(processed_actions);
    std::string action;
    while (iss >> action) {
        amount_of_actions++;
    }
    return amount_of_actions;
}

// Destructor
Server::~Server() = default;
