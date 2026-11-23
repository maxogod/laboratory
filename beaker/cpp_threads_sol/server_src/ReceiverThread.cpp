#include "ReceiverThread.h"

#include <utility>

#include "BroadcastListProtected.h"

ReceiverThread::ReceiverThread(Socket&& moved_socket, Queue<Command>& queue,
                               BroadcastListProtected& broadcast_list):
        protocol(std::move(moved_socket)),
        command_queue(queue),
        broadcast_list(broadcast_list),
        sender(SenderThread(protocol, broadcast_list)) {}

void ReceiverThread::run() {
    sender.start();
    while (_keep_running) {
        try {
            Command command = protocol.get_player_command();
            if (command == Command::NONE) {
                this->stop();
                continue;
            }
            command_queue.push(command);
        } catch (const SocketError& e) {
            continue;
        } catch (const ClosedQueue& e) {
            continue;
        }
    }
}

void ReceiverThread::stop() {
    if (!_keep_running) {
        return;
    }
    _keep_running = false;
    sender.stop();
    protocol.close_connection();
}

ReceiverThread::~ReceiverThread() { sender.join(); }
