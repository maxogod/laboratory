#include "ServerProtocol.h"

#include <utility>

#include <netinet/in.h>

#include "../common_src/defs.h"

ServerProtocol::ServerProtocol(Socket&& moved_socket): socket(std::move(moved_socket)) {}

ServerProtocol::ServerProtocol(ServerProtocol&& other) noexcept: socket(std::move(other.socket)) {}

ServerProtocol& ServerProtocol::operator=(ServerProtocol&& other) noexcept {
    if (this == &other) {
        return *this;
    }
    this->socket = std::move(other.socket);
    return *this;
}

void ServerProtocol::send_server_broadcast(const GameEvent& event) {
    uint8_t header = EVENT_HEADER;
    this->socket.send(&header, sizeof(uint8_t), true);

    uint16_t enemies_state[2] = {htons(event.enemies_alive), htons(event.enemies_dead)};
    this->socket.send(&enemies_state[0], sizeof(uint16_t) * 2, true);

    uint8_t event_type_int = event.event_type;
    this->socket.send(&event_type_int, sizeof(uint8_t), true);
}

Command ServerProtocol::get_player_command() {
    uint8_t action_code;
    int received = this->socket.receive(&action_code, sizeof(char), true);
    if (received == 0 || action_code != PLAYER_ATTACK_CODE) {
        return Command::NONE;
    }
    return Command::ATTACK;
}

void ServerProtocol::close_connection() {
    this->socket.shutdown();
    this->socket.close();
}

ServerProtocol::~ServerProtocol() = default;
