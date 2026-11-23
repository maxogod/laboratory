#include "Server.h"

#include <cstring>
#include <functional>
#include <iostream>
#include <queue>
#include <sstream>
#include <unordered_map>
#include <utility>
#include <vector>

#include "Game.h"
#include "PlayerAcceptor.h"

// Constructor
Server::Server(const std::string& port):
        player_acceptor(PlayerAcceptor(port, command_queue, broadcast_list)),
        game(Game(command_queue, broadcast_list)) {}

// Server methods
void Server::start_server() {
    accept_players();
    run_game();

    std::string input;
    while (std::cin >> input) {
        if (input == CLOSE_SERVER) {
            break;
        }
    }
}

void Server::accept_players() { this->player_acceptor.start(); }

void Server::run_game() { this->game.start(); }

// Destructor
Server::~Server() {
    this->player_acceptor.stop();
    this->game.stop();
    this->player_acceptor.join();
    this->game.join();
    command_queue.close();
}
