import socket
import threading


def receive_messages(sock, stop_event):
    while not stop_event.is_set():
        try:
            data = sock.recv(1024)

            if not data:
                if not stop_event.is_set():
                    print("Conexão encerrada pelo servidor.")
                break

            print('Recebido:', data.decode())

        except UnicodeDecodeError:
            print('Erro ao receber dados: mensagem inválida')
            break
        except OSError as e:
            if not stop_event.is_set():
                print('Erro ao receber dados:', e)
            break

    stop_event.set()


def send_messages(sock, stop_event):
    while not stop_event.is_set():
        try:
            message = input("> ")
        except (EOFError, KeyboardInterrupt):
            message = 'exit'

        if message.lower() == 'exit':
            break

        try:
            # O servidor separa comandos e apostas por linhas.
            sock.sendall((message + '\n').encode())
        except OSError as e:
            if not stop_event.is_set():
                print('Erro ao enviar dados:', e)
            break

    stop_event.set()
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def main():
    stop_event = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect(('localhost', 50007))
        except OSError as e:
            print('Não foi possível conectar ao servidor:', e)
            return

        print("Conectado ao servidor. Digite 'exit' para sair.")

        receive_thread = threading.Thread(
            target=receive_messages,
            args=(sock, stop_event)
        )

        receive_thread.start()

        send_thread = threading.Thread(
            target=send_messages,
            args=(sock, stop_event),
            daemon=True
        )

        send_thread.start()

        # A thread de entrada é daemon para não prender o processo caso o
        # servidor desconecte enquanto input() estiver bloqueado.
        receive_thread.join()

        stop_event.set()


if __name__ == "__main__":
    main()
