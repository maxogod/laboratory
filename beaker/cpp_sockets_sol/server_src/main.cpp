#include <iostream>

#include "Server.h"

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <port>" << std::endl;
        return 1;
    }

    Server server(argv[1]);
    int err = server.start_server();

    if (err) {
        std::cerr << "There was an error executing the server." << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
