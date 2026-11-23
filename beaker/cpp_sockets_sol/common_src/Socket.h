#ifndef TALLER_SOCKET_H
#define TALLER_SOCKET_H

#include <string>

#define CONNECTION_ATTEMPTS 10
#define CONNECTION_WAIT_LIST 10

class Socket {
private:
    int fd;
    bool is_skt_open;
    explicit Socket(int fd);

public:
    Socket();
    explicit Socket(const std::string& port);
    explicit Socket(const std::string& host, const std::string& port);

    // Cant copy sockets
    Socket(const Socket&) = delete;
    Socket& operator=(const Socket&) = delete;

    // Move sockets
    Socket(Socket&& other);
    Socket& operator=(Socket&& other);

    // Send and receive data
    // all_data = true means that all data must be sent/received
    // Returns the amount of bytes sent/received
    int send(const void* buffer, size_t length, bool all_data = true);
    int receive(void* buffer, size_t length, bool all_data = true);

    // Accept new connections
    Socket accept();

    // Returns whether the socket is open
    bool is_open() const;

    // Close the socket
    void close();

    ~Socket();
};


#endif  // TALLER_SOCKET_H
