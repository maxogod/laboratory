#ifndef TALLER_SERVER_H
#define TALLER_SERVER_H

#include <string>
#include <unordered_map>
#include <vector>

#include "../common_src/defs.h"
#include "../common_src/queue.h"

#include "BroadcastListProtected.h"
#include "Command.h"
#include "Game.h"
#include "PlayerAcceptor.h"

#define CLOSE_SERVER "q"

class Server {
private:
    Queue<Command> command_queue;
    BroadcastListProtected broadcast_list;
    PlayerAcceptor player_acceptor;
    Game game;

    void accept_players();
    void run_game();

public:
    explicit Server(const std::string& port);

    // Cant copy server
    Server(const Server&) = delete;
    Server& operator=(const Server&) = delete;

    // Cant move server
    Server(Server&& other) = delete;
    Server& operator=(Server&& other) = delete;

    void start_server();

    ~Server();
};


#endif  // TALLER_SERVER_H
