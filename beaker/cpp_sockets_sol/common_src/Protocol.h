#ifndef TALLER_PROTOCOL_H
#define TALLER_PROTOCOL_H

#include <string>
#include <unordered_map>
#include <vector>

#include "Socket.h"

#define CONNECTION_TERMINATED "CONNECTION_TERMINATED"

class Protocol {
private:
    Socket listening_socket;
    Socket client_socket;

public:
    Protocol();
    explicit Protocol(const std::string& port);
    explicit Protocol(const std::string& host, const std::string& port);

    // Cant copy protocols
    Protocol(const Protocol&) = delete;
    Protocol& operator=(const Protocol&) = delete;

    // Can move protocols
    Protocol(Protocol&& other);
    Protocol& operator=(Protocol&& other);

    // Send data
    int send_player_action(const std::string& action);
    int send_server_response(const std::string& response);

    // Receive data
    std::string get_player_action();
    std::string get_server_response();

    bool is_player_connected() const;

    ~Protocol();
};


#endif  // TALLER_PROTOCOL_H
