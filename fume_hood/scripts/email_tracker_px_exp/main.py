import socket
import threading


def acceptor(sock: socket.socket, stop_event: threading.Event):
    print("Accepting connections")
    sock.settimeout(1.0)
    while not stop_event.is_set():
        try:
            conn, addr = sock.accept()
            print("Connection from", addr)
            data = conn.recv(1024)
            print("Received", data)
            conn.sendall(b"HTTP/1.1 404 Not Found\n\nHello, World!")
            conn.close()
        except socket.timeout:
            continue
        except OSError:
            break


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("0.0.0.0", 3000))
    sock.listen(1)

    stop_event = threading.Event()
    acceptor_thread = threading.Thread(target=acceptor,
                                       args=(sock, stop_event))
    acceptor_thread.start()

    while True:
        user_input = input().strip().lower()
        if user_input == "q":
            print("Stopping server...")
            stop_event.set()
            sock.close()
            break

    acceptor_thread.join()


if __name__ == "__main__":
    main()
