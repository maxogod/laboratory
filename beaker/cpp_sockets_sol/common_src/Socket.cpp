#include "Socket.h"

#include <stdexcept>  // runtime_error

#include <arpa/inet.h>   // inet_addr
#include <errno.h>       // errno
#include <netinet/in.h>  // sockaddr_in
#include <sys/socket.h>
#include <unistd.h>  // close

#include "resolver.h"

// Constructors
Socket::Socket(): is_skt_open(false) { this->fd = -1; }

Socket::Socket(int fd): is_skt_open(true) { this->fd = fd; }

Socket::Socket(const std::string& port): is_skt_open(false) {
    Resolver resolver(nullptr, port.c_str(), true);

    while (resolver.has_next()) {
        struct addrinfo* addr = resolver.next();

        // Create a socket
        int fd = socket(addr->ai_family, addr->ai_socktype, addr->ai_protocol);
        if (fd == -1) {
            continue;
        }

        // Set socket options to reuse address and port
        int opt = 1;
        if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1) {
            ::close(fd);
            continue;
        }

        // Bind socket to port
        if (bind(fd, addr->ai_addr, addr->ai_addrlen) == -1) {
            ::close(fd);
            continue;
        }

        // Listen for incoming connections
        if (listen(fd, CONNECTION_WAIT_LIST) == -1) {
            ::close(fd);
            continue;
        }

        this->fd = fd;
        this->is_skt_open = true;
        return;
    }

    // Couldn't create server socket
    throw std::runtime_error("Error creating server socket");
}

Socket::Socket(const std::string& host, const std::string& port): is_skt_open(false) {
    Resolver resolver(host.c_str(), port.c_str(), false);

    // Resolve address and connect to server
    while (resolver.has_next()) {
        struct addrinfo* addr = resolver.next();

        // Create a socket
        int fd = socket(addr->ai_family, addr->ai_socktype, addr->ai_protocol);
        if (fd == -1) {
            continue;
        }

        // Connect to server
        int attempts = 0;
        while ((connect(fd, addr->ai_addr, addr->ai_addrlen) == -1) &&
               (attempts < CONNECTION_ATTEMPTS)) {
            attempts++;
        }

        if (attempts == CONNECTION_ATTEMPTS) {
            ::close(fd);
            continue;
        }

        this->fd = fd;
        this->is_skt_open = true;
        return;
    }

    // Couldn't connect to server
    throw std::runtime_error("Error connecting to server");
}

// Move sockets
Socket::Socket(Socket&& other) {
    this->fd = other.fd;
    other.fd = -1;
}

Socket& Socket::operator=(Socket&& other) {
    this->fd = other.fd;
    this->is_skt_open = other.is_skt_open;
    other.fd = -1;
    other.is_skt_open = false;
    return *this;
}

// Send and receive data
int Socket::send(const void* buffer, size_t length, bool all_data) {
    size_t total_sent = 0;
    do {
        int sent = ::send(this->fd, (char*)buffer + total_sent, length - total_sent, MSG_NOSIGNAL);
        if (sent == -1) {
            if (errno == EPIPE) {  // Connection closed by peer
                this->is_skt_open = false;
                break;
            }
            throw std::runtime_error("Error sending data");
        }
        total_sent += sent;
    } while (total_sent < length && all_data);

    return total_sent;
}

int Socket::receive(void* buffer, size_t length, bool all_data) {
    size_t total_received = 0;
    do {
        int received = ::recv(this->fd, (char*)buffer + total_received, length - total_received, 0);
        if (received == -1) {
            throw std::runtime_error("Error receiving data");
        }
        if (received == 0) {
            this->is_skt_open = false;
            break;
        }
        total_received += received;
    } while (total_received < length && all_data);

    return total_received;
}

// Accept new connections
Socket Socket::accept() {
    int new_fd = ::accept(this->fd, nullptr, nullptr);
    if (new_fd == -1) {
        throw std::runtime_error("Error accepting new connection");
    }

    return Socket(new_fd);
}

// Check if socket is open
bool Socket::is_open() const { return this->is_skt_open; }

// Close socket
void Socket::close() {
    if (this->fd == -1) {
        return;
    }
    ::close(this->fd);
    this->is_skt_open = false;
    this->fd = -1;
}

// Destructor
Socket::~Socket() {
    shutdown(this->fd, SHUT_RDWR);
    this->close();
}
