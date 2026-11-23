#ifndef TALLER_SENDERTHREAD_H
#define TALLER_SENDERTHREAD_H

#include <vector>

#include "../common_src/GameEvent.h"
#include "../common_src/Socket.h"
#include "../common_src/queue.h"
#include "../common_src/thread.h"

#include "BroadcastListProtected.h"
#include "ServerProtocol.h"

class SenderThread: public Thread {
private:
    ServerProtocol& protocol;
    BroadcastListProtected& broadcast_list;
    Queue<GameEvent> msg_queue;

public:
    SenderThread(ServerProtocol& protocol, BroadcastListProtected& broadcast_list);

    void run() override;

    void stop() override;

    ~SenderThread() override;
};


#endif  // TALLER_SENDERTHREAD_H
