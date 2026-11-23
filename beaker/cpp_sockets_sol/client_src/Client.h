#ifndef TALLER_CLIENT_H
#define TALLER_CLIENT_H

#include <string>

#include "../common_src/Protocol.h"

class Client {
private:
    Protocol protocol;
    std::string sv_host;
    std::string sv_port;
    std::string process_input(const std::string& input) const;
    void connect_to_server();

public:
    explicit Client(const std::string& host, const std::string& port);
    int start_client();
    ~Client();
};


#endif  // TALLER_CLIENT_H
