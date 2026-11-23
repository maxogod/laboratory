#ifndef TALLER_GAMEEVENT_H
#define TALLER_GAMEEVENT_H

#include <string>

#define EVENT_HEADER 0x06

enum EventType {
    ENEMY_DEATH = 0x04,
    ENEMY_REVIVE = 0x05,
};

class GameEvent {
public:
    uint16_t enemies_alive;
    uint16_t enemies_dead;
    EventType event_type;

    explicit GameEvent(uint16_t enemies_alive, uint16_t enemies_dead, EventType event_type);

    friend std::ostream& operator<<(std::ostream& os, const GameEvent& obj);

    ~GameEvent();
};


#endif  // TALLER_GAMEEVENT_H
