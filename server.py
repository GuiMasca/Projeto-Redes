import socket
import threading
import sys
import os
import time
from datetime import datetime

# o módulo loteria fica na pasta irmã "loteria/"; ajusta o sys.path para o
# interpretador encontrar "loteria.py" e "loteria_exceptions.py"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loteria'))

import loteria
from loteria_exceptions import LoteriaException

# protege as chamadas às funções de loteria, pois elas usam variáveis globais
lock_loteria = threading.Lock()
# protege a lista de conexões ativas, pois cada cliente roda em sua própria thread
lock_clientes = threading.Lock()
# protege o envio pelos sockets, pois várias threads podem enviar ao mesmo tempo
lock_envio = threading.Lock()

# conexões ativas; a sessão de loteria é única e compartilhada por todos
clientes = []

# flag global que coordena o encerramento do servidor e das threads
servidor_ativo = True

HOST = ''
PORT = 50007
# intervalo (em segundos) entre os sorteios; extraído para constante para
# acelerar os testes de integração (é só reduzir o valor durante os testes)
TEMPO_SORTEIO = 60


def processar_mensagem(texto):
    """Interpreta o texto cru do cliente e chama a função correspondente do módulo loteria.

    - Começa com ":" -> comando de configuração (:inicio, :fim, :qtd).
    - Caso contrário -> aposta (números separados por espaço).

    Retorna a string de resposta. Isolada do socket para poder ser testada sem rede.
    """
    texto = texto.strip()

    with lock_loteria:
        try:
            if texto.startswith(':inicio'):
                valor = int(texto.split()[1])
                return loteria.set_min_value(valor)

            elif texto.startswith(':fim'):
                valor = int(texto.split()[1])
                return loteria.set_max_value(valor)

            elif texto.startswith(':qtd'):
                valor = int(texto.split()[1])
                return loteria.qtd_numeros_sorteador(valor)

            else:
                # não começa com ":" -> é uma aposta
                return loteria.add_ticket(texto)

        except LoteriaException as e:
            return f"ERRO: {e}"
        except (ValueError, IndexError):
            return "ERRO: Comando mal formatado"


def montar_mensagem_resultado(sorteados, vencedores):
    """Monta a string de resultado: números sorteados e, por aposta vencedora, quais números acertou."""
    linha_sorteio = f"Números sorteados: {sorted(sorteados)}"

    sorteados_set = set(sorteados)

    linha_vencedores = []
    # WINNER_TICKETS é uma lista onde o índice é a quantidade de acertos
    for qtd_acertos, tickets in enumerate(vencedores):
        if qtd_acertos == 0 or not tickets:
            continue
        for ticket in tickets:
            # cada aposta é um set de ints; mostra a interseção com o sorteio
            acertados = sorted(sorteados_set & ticket)
            linha_vencedores.append(f"Aposta {sorted(ticket)} acertou {qtd_acertos} número(s): {acertados}")

    if not linha_vencedores:
        linha_vencedores.append("Nenhum vencedor nesta rodada.")

    return linha_sorteio + "\n" + "\n".join(linha_vencedores)


def enviar(conn, texto):
    """Envia um texto ao cliente garantindo o delimitador '\n' no final.

    O TCP é um fluxo de bytes sem fronteiras de mensagem: sem um delimitador
    consistente, respostas consecutivas podem chegar agrupadas no cliente.
    """
    if not texto.endswith('\n'):
        texto += '\n'

    with lock_envio:
        conn.sendall(texto.encode())


def broadcast(texto):
    """Envia uma mensagem a todos os clientes conectados; descarta quem falhar."""
    with lock_clientes:
        destinatarios = list(clientes)

    for conn in destinatarios:
        try:
            enviar(conn, texto)
        except OSError:
            remover_cliente(conn)


def remover_cliente(conn):
    """Tira a conexão da lista de clientes e fecha o socket (é idempotente)."""
    with lock_clientes:
        if conn in clientes:
            clientes.remove(conn)

    try:
        conn.close()
    except OSError:
        pass


def thread_receber_cliente(conn, addr):
    """Loop de leitura de UM cliente.

    O TCP não garante que uma linha completa chegue em um único recv(), então
    acumula os blocos recebidos em um buffer e só processa até o último '\n',
    preservando a fração final da linha que ainda está incompleta.
    """
    try:
        horario = datetime.now().strftime("%H:%M:%S")
        enviar(conn, f"{horario}: CONECTADO!!")

        buffer = ""

        while servidor_ativo:
            try:
                dados = conn.recv(1024)
            except OSError:
                break

            if not dados:
                # recv() retornou vazio -> cliente fechou a conexão
                break

            buffer += dados.decode(errors="replace")

            while '\n' in buffer:
                linha, buffer = buffer.split('\n', 1)

                if not linha.strip():
                    continue

                print(f"Recebido de {addr}: {linha}")

                try:
                    resposta = processar_mensagem(linha)
                except Exception as e:
                    print(f"[Cliente {addr}] Erro ao processar mensagem: {e}")
                    resposta = "ERRO: Ocorreu um problema interno do servidor."

                try:
                    enviar(conn, resposta)
                except OSError:
                    return

    finally:
        remover_cliente(conn)
        print(f"Cliente desconectado: {addr}")


def thread_sorteio():
    """A cada TEMPO_SORTEIO segundos: sorteia, transmite o resultado a todos os clientes e zera as apostas."""
    while servidor_ativo:
        # dorme em passos de 1s para reagir rápido ao encerramento do servidor
        for _ in range(TEMPO_SORTEIO):
            if not servidor_ativo:
                return
            time.sleep(1)

        try:
            with lock_loteria:
                loteria.temp_numbers_sort()
                sorteados = loteria.SORTED_NUMBERS
                vencedores = loteria.WINNER_TICKETS
                # zera a lista de apostas para o próximo ciclo
                loteria.TICKETS.clear()

            mensagem = montar_mensagem_resultado(sorteados, vencedores)

        except Exception as e:
            print(f"[Sorteio] Erro ao realizar sorteio: {e}")
            continue

        print("Sorteio realizado:", sorted(sorteados))
        broadcast(mensagem)


if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)

        # sessão única e compartilhada: começa do zero a cada execução do servidor
        with lock_loteria:
            loteria.reset_all()

        print(f"Servidor aguardando conexões na porta {PORT}... (Ctrl+C para encerrar)")

        threading.Thread(target=thread_sorteio, daemon=True).start()

        try:
            # aceita clientes em paralelo: cada conexão ganha sua própria thread
            # de leitura e continua participando da mesma sessão de loteria
            while True:
                conn, addr = s.accept()
                print('Conectado por', addr)

                with lock_clientes:
                    clientes.append(conn)

                threading.Thread(
                    target=thread_receber_cliente,
                    args=(conn, addr),
                    daemon=True
                ).start()

        except KeyboardInterrupt:
            print("\nCtrl+C recebido: encerrando o servidor...")
        finally:
            servidor_ativo = False

            with lock_clientes:
                for c in clientes:
                    try:
                        c.close()
                    except OSError:
                        pass
                clientes.clear()

            print("Servidor encerrado.")
