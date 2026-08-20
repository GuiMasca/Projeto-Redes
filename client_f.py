import socket
import threading


def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024)

            if not data:
                break

            print('Recebido:', data.decode())

        except Exception as e:
            print('Erro ao receber dados', e)
            break


def send_messages(sock):
    while True:
        message = input("> ")

        if message.lower() == 'exit':
            break

        sock.sendall(message.encode())


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect(('localhost', 12345))

    print("Conectado ao servidor. Digite 'exit' para sair.")

    receive_thread = threading.Thread(
        target=receive_messages,
        args=(sock,)
    )

    receive_thread.start()

    send_thread = threading.Thread(
        target=send_messages,
        args=(sock,)
    )

    send_thread.start()

    send_thread.join()

    sock.close()


if __name__ == "__main__":
    main()