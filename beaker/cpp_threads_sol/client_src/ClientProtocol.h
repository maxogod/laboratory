#ifndef TALLER_CLIENTPROTOCOL_H
#define TALLER_CLIENTPROTOCOL_H

#include <string>
#include <vector>

#include "../common_src/GameEvent.h"
#include "../common_src/Socket.h"

class ClientProtocol {
private:
    Socket socket;

public:
    explicit ClientProtocol(const std::string& host, const std::string& port);

    // Cant copy protocols
    ClientProtocol(const ClientProtocol&) = delete;
    ClientProtocol& operator=(const ClientProtocol&) = delete;

    // Can move protocols
    ClientProtocol(ClientProtocol&& other) noexcept;
    ClientProtocol& operator=(ClientProtocol&& other) noexcept;

    // Send/Receive data
    void send_player_attack();
    std::vector<GameEvent> get_server_broadcast(int amount_of_msg);

    bool is_player_connected() const;

    ~ClientProtocol();
};


#endif  // TALLER_CLIENTPROTOCOL_H
