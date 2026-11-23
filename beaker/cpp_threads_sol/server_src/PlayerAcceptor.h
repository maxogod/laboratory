#ifndef TALLER_PLAYERACCEPTOR_H
#define TALLER_PLAYERACCEPTOR_H

#include <list>
#include <string>
#include <utility>

#include "../common_src/Socket.h"
#include "../common_src/queue.h"
#include "../common_src/thread.h"

#include "BroadcastListProtected.h"
#include "Command.h"
#include "ReceiverThread.h"
#include "SenderThread.h"

class PlayerAcceptor: public Thread {
private:
    Socket listening_socket;
    Queue<Command>& command_queue;
    BroadcastListProtected& broadcast_list;
    std::list<ReceiverThread> players;

    // Accept players
    void accept_players();

    // Remove stopped threads
    void reap_dead_players();

public:
    PlayerAcceptor(const std::string& port, Queue<Command>& queue,
                   BroadcastListProtected& broadcast_list);

    // Cant copy acceptor
    PlayerAcceptor(const PlayerAcceptor&) = delete;
    PlayerAcceptor& operator=(const PlayerAcceptor&) = delete;

    // Cant move acceptor
    PlayerAcceptor(PlayerAcceptor&& other) = delete;
    PlayerAcceptor& operator=(PlayerAcceptor&& other) = delete;

    // Run the acceptor
    void run() override;

    void stop() override;

    ~PlayerAcceptor() override;
};


#endif  // TALLER_PLAYERACCEPTOR_H
