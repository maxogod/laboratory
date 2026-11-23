#ifndef TALLER_SERVER_H
#define TALLER_SERVER_H

#include <string>
#include <unordered_map>
#include <vector>

#include "../common_src/Protocol.h"

class Server {
private:
    // In-game possible actions and combos
    std::unordered_map<std::string, std::string> possible_combos = {
            {"JUMP JUMP HIT", "UPPERCUT"},
            {"HIT DUCK LEFT", "SIDEKICK"},
            {"LEFT RIGHT JUMP HIT", "HIGHKICK"},
    };
    std::string sv_port;
    Protocol protocol;
    std::string process_player_actions(std::string& combo);
    static int count_processed_actions(const std::string& processed_actions);
    void accept_players();

public:
    explicit Server(const std::string& port);
    int start_server();
    ~Server();
};


#endif  // TALLER_SERVER_H
