#ifndef TALLER_RECEIVERTHREAD_H
#define TALLER_RECEIVERTHREAD_H

#include "../common_src/Socket.h"
#include "../common_src/queue.h"
#include "../common_src/thread.h"

#include "BroadcastListProtected.h"
#include "Command.h"
#include "SenderThread.h"
#include "ServerProtocol.h"

class ReceiverThread: public Thread {
private:
    ServerProtocol protocol;
    Queue<Command>& command_queue;
    BroadcastListProtected& broadcast_list;
    SenderThread sender;

public:
    ReceiverThread(Socket&& socket, Queue<Command>& queue, BroadcastListProtected& broadcast_list);

    void run() override;

    void stop() override;

    ~ReceiverThread() override;
};


#endif  // TALLER_RECEIVERTHREAD_H
