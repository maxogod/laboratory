#include "BroadcastListProtected.h"

#include <mutex>
#include <vector>

#include "../common_src/queue.h"

BroadcastListProtected::BroadcastListProtected() = default;

void BroadcastListProtected::add_queue(Queue<GameEvent>& queue) {
    std::unique_lock<std::mutex> lock(m);
    broadcast_list.push_back(queue);
}

void BroadcastListProtected::remove_queue(Queue<GameEvent>& queue) {
    std::unique_lock<std::mutex> lock(m);
    broadcast_list.remove_if([&queue](const std::reference_wrapper<Queue<GameEvent>>& q) {
        return &q.get() == &queue;
    });
}

void BroadcastListProtected::broadcast(const GameEvent& event) {
    std::lock_guard<std::mutex> lock(m);
    for (auto& queue: broadcast_list) {
        queue.get().try_push(event);
    }
}

BroadcastListProtected::~BroadcastListProtected() = default;
