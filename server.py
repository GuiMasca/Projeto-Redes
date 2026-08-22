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

# protege chamadas às funções de loteria, pois elas usam variáveis globais
lock = threading.Lock()
# protege o envio pelo socket, pois as duas threads podem enviar ao mesmo tempo
lock_envio = threading.Lock()
# flag global que coordena o encerramento das duas threads
rodando = True

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

    with lock:
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

    return linha_sorteio + "\n" + "\n".join(linha_vencedores) + "\n"


def thread_1_receber_dados(conn, addr):
    """Loop de leitura do socket: interpreta cada mensagem recebida e responde via sendall."""
    global rodando

    while rodando:
        try:
            dados = conn.recv(1024)
        except OSError:
            # erro de rede: cliente desconectou ou socket foi fechado
            break

        if not dados:
            # recv() retornou vazio -> cliente fechou a conexão
            break

        texto = dados.decode()

        # o TCP pode agrupar várias mensagens numa única chegada de dados;
        # separa por linha para interpretar cada comando/aposta individualmente
        for linha in texto.splitlines():
            if not linha.strip():
                continue

            print(f"Recebido de {addr}: {linha}")

            try:
                resposta = processar_mensagem(linha)
            except Exception as e:
                print(f"[Thread 1] Erro ao processar mensagem: {e}")
                resposta = "ERRO: Ocorreu um problema interno do servidor."

            with lock_envio:
                try:
                    conn.sendall(resposta.encode())
                except OSError:
                    rodando = False
                    break

    rodando = False

    print("thread 1 encerrada")


def thread_2_sorteio(conn):
    """A cada TEMPO_SORTEIO segundos: sorteia, monta o resultado, envia ao cliente e zera as apostas."""
    global rodando

    while rodando:
        # dorme em passos de 1s para reagir rápido se a conexão cair no meio da espera
        for _ in range(TEMPO_SORTEIO):
            if not rodando:
                break
            time.sleep(1)

        if not rodando:
            break

        try:
            with lock:
                loteria.temp_numbers_sort()
                sorteados = loteria.SORTED_NUMBERS
                vencedores = loteria.WINNER_TICKETS
                # zera a lista de apostas para o próximo ciclo
                loteria.TICKETS.clear()

            mensagem = montar_mensagem_resultado(sorteados, vencedores)

        except Exception as e:
            print(f"[Thread 2] Erro ao realizar sorteio: {e}")
            continue

        with lock_envio:
            try:
                conn.sendall(mensagem.encode())
            except OSError:
                rodando = False
                break

    print("thread 2 encerrada")


if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)

        # aceita clientes em sequência: quando um usuário desconecta,
        # o servidor volta a aguardar a próxima conexão
        while True:
            print("Servidor aguardando conexão...")

            conn, addr = s.accept()

            with conn:
                print('Conectado por', addr)

                horario = datetime.now().strftime("%H:%M:%S")
                msg1 = f"{horario}: CONECTADO!!"
                conn.sendall(msg1.encode())

                print("MSG1 enviada:", msg1)

                # novo usuário começa sem as apostas da sessão anterior
                with lock:
                    loteria.reset_tickets()

                # reinicia a flag que coordena o encerramento das threads
                rodando = True

                t1 = threading.Thread(target=thread_1_receber_dados, args=(conn, addr))
                t2 = threading.Thread(target=thread_2_sorteio, args=(conn,))

                t1.start()
                t2.start()

                # aguarda as duas threads encerrarem antes do próximo accept
                t1.join()
                t2.join()

            print("Cliente desconectado.")