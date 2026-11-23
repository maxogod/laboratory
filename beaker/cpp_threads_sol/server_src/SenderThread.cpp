#include "SenderThread.h"

#include <vector>

#include "../common_src/queue.h"

SenderThread::SenderThread(ServerProtocol& protocol, BroadcastListProtected& broadcast_list):
        protocol(protocol), broadcast_list(broadcast_list) {
    broadcast_list.add_queue(msg_queue);
}

void SenderThread::run() {
    while (_keep_running) {
        // Send message
        try {
            GameEvent event = msg_queue.pop();
            protocol.send_server_broadcast(event);
        } catch (const ClosedQueue& e) {
            continue;
        }
    }
}

void SenderThread::stop() {
    _keep_running = false;
    msg_queue.close();
}

SenderThread::~SenderThread() { broadcast_list.remove_queue(msg_queue); }
