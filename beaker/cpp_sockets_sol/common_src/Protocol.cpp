#include "Protocol.h"

#include <stdexcept>
#include <utility>

#include <netinet/in.h>

#include "Serializer.h"

// Constructors
Protocol::Protocol() = default;

Protocol::Protocol(const std::string& port): listening_socket(port) {
    this->client_socket = this->listening_socket.accept();
}

Protocol::Protocol(const std::string& host, const std::string& port): client_socket(host, port) {}

// can be moved
Protocol::Protocol(Protocol&& other) {
    this->listening_socket = std::move(other.listening_socket);
    this->client_socket = std::move(other.client_socket);
}

Protocol& Protocol::operator=(Protocol&& other) {
    if (this == &other) {
        return *this;
    }
    this->listening_socket = std::move(other.listening_socket);
    this->client_socket = std::move(other.client_socket);
    return *this;
}

// Send data
int Protocol::send_player_action(const std::string& actions) {

    std::vector<uint8_t> serialized_actions = Serializer::serialize(actions);
    size_t len_to_send = serialized_actions.size();
    try {
        this->client_socket.send(&serialized_actions[0], len_to_send, true);
    } catch (const std::runtime_error& e) {
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

int Protocol::send_server_response(const std::string& processed_actions) {
    uint16_t len = processed_actions.size();
    len = htons(len);
    try {  // send the length of the processed actions
        this->client_socket.send((char*)&len, sizeof(uint16_t), true);
    } catch (const std::runtime_error& e) {
        return EXIT_FAILURE;
    }

    try {  // send the processed actions
        this->client_socket.send(processed_actions.c_str(), processed_actions.size() * sizeof(char),
                                 true);
    } catch (const std::runtime_error& e) {
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

// Receive data
std::string Protocol::get_player_action() {
    std::vector<uint8_t> actions;
    uint8_t current_byte;
    while (true) {
        try {
            this->client_socket.receive(&current_byte, sizeof(char), true);
        } catch (const std::runtime_error& e) {
            return CONNECTION_TERMINATED;
        }
        if (current_byte == NOP) {
            break;
        }
        actions.push_back(current_byte);
    }

    if (actions.empty()) {  // connection was terminated with no errors
        return CONNECTION_TERMINATED;
    }

    std::string deserialized_actions = Serializer::deserialize(actions);
    return deserialized_actions;
}

std::string Protocol::get_server_response() {
    uint16_t len;
    try {  // get length
        this->client_socket.receive((char*)&len, sizeof(uint16_t), true);
    } catch (const std::runtime_error& e) {
        return CONNECTION_TERMINATED;
    }
    len = ntohs(len);

    std::vector<char> response(len);
    try {  // get response
        this->client_socket.receive(&response[0], len * sizeof(char), true);
    } catch (const std::runtime_error& e) {
        return CONNECTION_TERMINATED;
    }

    if (response.empty()) {  // connection was terminated with no errors
        return CONNECTION_TERMINATED;
    }

    std::string response_str(response.begin(), response.end());
    return response_str;
}

bool Protocol::is_player_connected() const { return this->client_socket.is_open(); }

// Destructor
Protocol::~Protocol() = default;
