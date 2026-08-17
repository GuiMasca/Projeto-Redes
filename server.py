import socket
import threading
import sys
import os
import time
from datetime import datetime

import loteria
from loteria_exceptions import LoteriaException

# protege chamadas as funções de loteria, pois elas usam variáveis globais
lock = threading.Lock()
lock_envio = threading.Lock()
rodando = True

HOST = ''
PORT = 50007


def processar_mensagem(texto): #tradutor
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

    linha_sorteio = f"Numeros serteados: {sorted(sorteados)}"

    linha_vencedores = []
    for qtd_acertos, tickets in vencedores.items():
        if tickets:
            linha_vencedores.append(f"{qtd_acertos} acertos: {', '.join(tickets)}")

        if not linha_vencedores:
            linha_vencedores.append("Nenhum vencedor nesta rodada.")

        return linha_sorteio + "\n" + "\n".join(linha_vencedores) + "\n"

def thread_1_receber_dados(conn):

    global rodando

    while rodando:
        try:
            dados = conn.recv(1024)

        except OSError:
            break

        if not dados:
            break

        texto = dados.decode()
        resposta = processar_mensagem(texto)

        with lock_envio:
            try:
                conn.sendall(resposta.encode())
            except OSError:
                break

    rodando = False

    print("thread 1 encerrada")

def thread_2_sorteio(conn):

    global rodando

    while rodando:
        for _ in range(60):
            if not rodando:
                break
            time.sleep(1)

        if not rodando:
            break

        with lock:
            loteria.temp_numbers_sort()
            sorteados = loteria.SORTED_NUMBERS
            vencedores = loteria.WINNER_TICKETS

        mensagem = montar_mensagem_resultado(sorteados, vencedores)

        with lock_envio:
            try:
                conn.sendall(mensagem.encode())
            except OSError:
                rodando = False
                break

if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)

        print("Servidor aguardando conexão...")

        conn, addr = s.accept()

        with conn:
            print('Conectado por', addr)

            horario = datetime.now().strftime("%H:%M:%S")
            msg1 = f"{horario}: CONECTADO!!"
            conn.sendall(msg1.encode())

            print("MSG1 enviada:", msg1)

            t1 = threading.Thread(target=thread_1_receber_dados, args=(conn,))
            t2 = threading.Thread(target=thread_2_sorteio, args=(conn,))

            t1.start()
            t2.start()

            t1.join()
            t2.join()

    print("Servidor encerrado.")