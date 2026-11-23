#include "ClientProtocol.h"

#include <utility>
#include <vector>

#include <netinet/in.h>

#include "../common_src/defs.h"

ClientProtocol::ClientProtocol(const std::string& host, const std::string& port):
        socket(host, port) {}

ClientProtocol::ClientProtocol(ClientProtocol&& other) noexcept: socket(std::move(other.socket)) {}

ClientProtocol& ClientProtocol::operator=(ClientProtocol&& other) noexcept {
    if (this == &other) {
        return *this;
    }
    this->socket = std::move(other.socket);
    return *this;
}

void ClientProtocol::send_player_attack() {
    uint8_t attack = PLAYER_ATTACK_CODE;
    this->socket.send(&attack, sizeof(uint8_t), true);
}

std::vector<GameEvent> ClientProtocol::get_server_broadcast(int amount_of_msg) {
    std::vector<GameEvent> events;
    for (int i = 0; i < amount_of_msg; i++) {
        uint8_t header;
        int received = this->socket.receive(&header, sizeof(uint8_t), true);

        uint16_t enemies_state[2];
        received += this->socket.receive(&enemies_state[0], sizeof(uint16_t) * 2, true);

        uint8_t event_type_int;
        received += this->socket.receive(&event_type_int, sizeof(uint8_t), true);

        if (received == 0) {
            break;  // Connection was terminated by server
        }

        auto event_type = static_cast<EventType>(event_type_int);

        events.emplace_back(ntohs(enemies_state[0]), ntohs(enemies_state[1]), event_type);
    }

    return events;
}

bool ClientProtocol::is_player_connected() const { return this->socket.is_open(); }

ClientProtocol::~ClientProtocol() = default;
