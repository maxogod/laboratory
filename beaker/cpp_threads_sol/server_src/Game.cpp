#include "Game.h"

#include <chrono>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#include <arpa/inet.h>

#include "../common_src/GameEvent.h"
#include "../common_src/defs.h"
#include "../common_src/queue.h"

#include "BroadcastListProtected.h"
#include "Command.h"

Game::Game(Queue<Command>& queue, BroadcastListProtected& broadcast_list):
        command_queue(queue), broadcast_list(broadcast_list), enemies(NUMBER_ENEMIES) {}

void Game::run() { game_loop(); }

void Game::game_loop() {
    while (this->_keep_running) {

        bool incoming_commands = true;
        while (incoming_commands) {
            Command cmd = Command::NONE;
            incoming_commands =
                    this->command_queue.try_pop(cmd);  // Non-blocking pop, puts result in cmd
            if (cmd == Command::ATTACK) {
                this->process_player_attack();
            }
        }

        this->process_enemy_revive();
        this->sleep_delta();
    }
}

// Game events
void Game::process_player_attack() {
    if (this->enemies_alive == 0) {
        return;
    }
    for (auto& enemy: this->enemies) {
        if (enemy.is_alive()) {
            enemy.die();
            this->enemies_alive--;
            log_event(ENEMY_DEATH);
            break;
        }
    }
}

void Game::process_enemy_revive() {
    if (this->enemies_alive == NUMBER_ENEMIES) {
        return;
    }
    for (auto& enemy: this->enemies) {
        bool revived = enemy.try_revive();
        if (revived) {
            this->enemies_alive++;
            log_event(ENEMY_REVIVE);
        }
    }
}

void Game::log_event(const EventType& event_type) const {
    GameEvent event(this->enemies_alive, NUMBER_ENEMIES - this->enemies_alive, event_type);
    broadcast_list.broadcast(event);
    std::cout << event << std::endl;
}

// Sleep for delta time
void Game::sleep_delta() const {
    auto milliseconds_to_sleep = std::chrono::milliseconds(DELTA);
    std::this_thread::sleep_for(milliseconds_to_sleep);
}

Game::~Game() = default;
