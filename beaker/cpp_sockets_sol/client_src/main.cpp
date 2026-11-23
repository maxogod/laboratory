#include <iostream>

#include "../common_src/Protocol.h"
#include "../common_src/Serializer.h"

#include "Client.h"

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <host> <port>" << std::endl;
        return 1;
    }

    Client client(argv[1], argv[2]);
    int err = client.start_client();

    if (err) {
        std::cerr << "There was an error executing the client." << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
