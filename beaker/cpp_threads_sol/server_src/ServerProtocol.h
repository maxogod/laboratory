#ifndef TALLER_SERVERPROTOCOL_H
#define TALLER_SERVERPROTOCOL_H

#include <vector>

#include "../common_src/GameEvent.h"
#include "../common_src/Socket.h"

#include "Command.h"

class ServerProtocol {
private:
    Socket socket;

public:
    explicit ServerProtocol(Socket&& moved_socket);

    // Cant copy protocols
    ServerProtocol(const ServerProtocol&) = delete;
    ServerProtocol& operator=(const ServerProtocol&) = delete;

    // Can move protocols
    ServerProtocol(ServerProtocol&& other) noexcept;
    ServerProtocol& operator=(ServerProtocol&& other) noexcept;

    // Send/Receive data
    void send_server_broadcast(const GameEvent& event);
    Command get_player_command();

    void close_connection();

    ~ServerProtocol();
};


#endif  // TALLER_SERVERPROTOCOL_H
