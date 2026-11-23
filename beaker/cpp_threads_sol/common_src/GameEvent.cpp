#include "GameEvent.h"

GameEvent::GameEvent(uint16_t enemies_alive, uint16_t enemies_dead, EventType event_type):
        enemies_alive(enemies_alive), enemies_dead(enemies_dead), event_type(event_type) {}

std::ostream& operator<<(std::ostream& os, const GameEvent& obj) {
    std::string result;
    switch (obj.event_type) {
        case ENEMY_DEATH:
            result += "Un enemigo ha muerto. " + std::to_string(obj.enemies_alive) + " vivo(s) y " +
                      std::to_string(obj.enemies_dead) + " muerto(s).";
            break;
        case ENEMY_REVIVE:
            result += "Un enemigo ha revivido. " + std::to_string(obj.enemies_alive) +
                      " vivo(s) y " + std::to_string(obj.enemies_dead) + " muerto(s).";
            break;
    }
    os << result;
    return os;
}

GameEvent::~GameEvent() = default;
