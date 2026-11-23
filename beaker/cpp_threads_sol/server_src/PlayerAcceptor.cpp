#include "PlayerAcceptor.h"

#include <string>

#include "../common_src/queue.h"

#include "ReceiverThread.h"
#include "ServerProtocol.h"

PlayerAcceptor::PlayerAcceptor(const std::string& port, Queue<Command>& queue,
                               BroadcastListProtected& broadcast_list):
        listening_socket(port), command_queue(queue), broadcast_list(broadcast_list) {}

void PlayerAcceptor::accept_players() {
    while (_keep_running) {
        try {
            // Accept player
            Socket player_socket = listening_socket.accept();

            // Create player threads giving them the socket ownership
            players.emplace_back(std::move(player_socket), command_queue, broadcast_list);

            // Start player threads
            players.back().start();

            // Remove stopped threads
            reap_dead_players();
        } catch (const SocketError& e) {
            continue;
        }
    }
}

void PlayerAcceptor::reap_dead_players() {
    players.remove_if([](ReceiverThread& player) {
        if (!player.is_alive()) {
            player.join();
            return true;
        }
        return false;
    });
}

void PlayerAcceptor::run() { accept_players(); }

void PlayerAcceptor::stop() {
    _keep_running = false;
    listening_socket.shutdown();
    listening_socket.close();
}

PlayerAcceptor::~PlayerAcceptor() {
    for (auto& player: players) {
        player.stop();
        player.join();
    }
}
