import socket
import threading


def show_bet_prompt():
    print('Faça sua aposta:')
    print('> ', end='', flush=True)


def receive_messages(sock, stop_event, bet_allowed):
    while not stop_event.is_set():
        try:
            data = sock.recv(1024)

            if not data:
                if not stop_event.is_set():
                    print("Conexão encerrada pelo servidor.")
                break

            message = data.decode()
            print('\nRecebido:', message)

            if 'foi adicionada com sucesso' in message:
                print('Aposta confirmada! Aguarde os resultados do sorteio.')
            elif 'Números sorteados:' in message:
                print('Rodada encerrada. Uma nova aposta pode ser feita.')
                bet_allowed.set()
                show_bet_prompt()
            elif 'ERRO:' in message:
                # A aposta não foi aceita; libera uma nova tentativa.
                bet_allowed.set()
                show_bet_prompt()

        except UnicodeDecodeError:
            print('Erro ao receber dados: mensagem inválida')
            break
        except OSError as e:
            if not stop_event.is_set():
                print('Erro ao receber dados:', e)
            break

    stop_event.set()


def send_messages(sock, stop_event, bet_allowed):
    while not stop_event.is_set():
        bet_allowed.wait()
        if stop_event.is_set():
            break

        try:
            message = input()
        except (EOFError, KeyboardInterrupt):
            message = 'exit'

        if message.lower() == 'exit':
            break

        # Impede outra aposta até o servidor rejeitar a atual ou realizar o
        # sorteio. Assim o cliente permanece no estado "aguarde".
        bet_allowed.clear()

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
    bet_allowed = threading.Event()
    bet_allowed.set()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect(('localhost', 50007))
        except OSError as e:
            print('Não foi possível conectar ao servidor:', e)
            return

        try:
            initial_message = sock.recv(1024)
            if not initial_message:
                print('Conexão encerrada pelo servidor.')
                return
            print('Recebido:', initial_message.decode())
        except UnicodeDecodeError:
            print('Erro ao receber dados: mensagem inválida')
            return
        except OSError as e:
            print('Erro ao receber dados:', e)
            return

        print("Conectado ao servidor. Digite 'exit' para sair.")
        print("\nCOMO JOGAR")
        print("- Faça sua aposta digitando 5 números separados por espaços.")
        print("  Exemplo: 1 2 3 4 5")
        print("- Após a confirmação da aposta, aguarde o resultado do sorteio.\n")
        show_bet_prompt()

        receive_thread = threading.Thread(
            target=receive_messages,
            args=(sock, stop_event, bet_allowed)
        )

        receive_thread.start()

        send_thread = threading.Thread(
            target=send_messages,
            args=(sock, stop_event, bet_allowed),
            daemon=True
        )

        send_thread.start()

        # A thread de entrada é daemon para não prender o processo caso o
        # servidor desconecte enquanto input() estiver bloqueado.
        receive_thread.join()

        stop_event.set()


if __name__ == "__main__":
    main()
