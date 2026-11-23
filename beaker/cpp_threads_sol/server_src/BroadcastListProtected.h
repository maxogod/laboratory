#ifndef TALLER_BROADCASTLISTPROTECTED_H
#define TALLER_BROADCASTLISTPROTECTED_H

#include <functional>
#include <list>
#include <mutex>
#include <vector>

#include "../common_src/GameEvent.h"
#include "../common_src/queue.h"

class BroadcastListProtected {
private:
    std::list<std::reference_wrapper<Queue<GameEvent>>> broadcast_list;
    std::mutex m;

public:
    BroadcastListProtected();

    void add_queue(Queue<GameEvent>& queue);
    void remove_queue(Queue<GameEvent>& queue);

    void broadcast(const GameEvent& event);

    ~BroadcastListProtected();
};


#endif  // TALLER_BROADCASTLISTPROTECTED_H
