#ifndef TALLER_GAME_H
#define TALLER_GAME_H

#include <vector>

#include "../common_src/defs.h"
#include "../common_src/queue.h"
#include "../common_src/thread.h"

#include "BroadcastListProtected.h"
#include "Command.h"
#include "Enemy.h"

#define NUMBER_ENEMIES 5
#define DELTA 200

class Game: public Thread {
private:
    Queue<Command>& command_queue;
    BroadcastListProtected& broadcast_list;
    std::vector<Enemy> enemies;
    int enemies_alive = NUMBER_ENEMIES;

    // Game events
    void process_player_attack();
    void process_enemy_revive();
    void log_event(const EventType& event_type) const;

    // Sleep for delta time
    void sleep_delta() const;
    // Main game loop
    void game_loop();

public:
    explicit Game(Queue<Command>& queue, BroadcastListProtected& broadcast_list);
    // Cant copy game
    Game(const Game&) = delete;
    Game& operator=(const Game&) = delete;

    // Cant move game
    Game(Game&& other) = delete;
    Game& operator=(Game&& other) = delete;

    // Run the game
    void run() override;

    ~Game() override;
};


#endif  // TALLER_GAME_H
