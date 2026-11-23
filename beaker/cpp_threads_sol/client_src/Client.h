#ifndef TALLER_CLIENT_H
#define TALLER_CLIENT_H

#include <string>

#include "ClientProtocol.h"

#define ATTACK_STR "ATACAR"
#define READ_STR "LEER"
#define EXIT_STR "SALIR"

class Client {
private:
    ClientProtocol protocol;

    // Handle player input
    std::string get_command();
    int get_amount_of_msg_to_read();

public:
    explicit Client(const std::string& host, const std::string& port);

    void start_client();

    ~Client();
};


#endif  // TALLER_CLIENT_H
