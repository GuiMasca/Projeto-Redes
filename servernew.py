import socket
import threading
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loteria')) #esta linha só serve para que o python leia a pasta da loteria

import loteria
from datetime import datetime
from loteria_exceptions import LoteriaException, AddTicketException


lock = threading.Lock()
lock_envio = threading.Lock()

def ciclo_sorteio(conn, encerrar):
    while True:
        for _ in range(60): #dorme por 60 segundos, em 60 sonos de 1 segundo
            if encerrar.is_set():
                return
            time.sleep(1)   #sono de 1 segundo

        with lock:
            vencedores = loteria.temp_numbers_sort()    #sorteia e calcula
            sorteados = loteria.SORTED_NUMBERS  #guarda cópia dos sorteados
            loteria.TICKETS.clear() #zera as apostas para o proximo ciclo
        mensagem = montar_mensagem_resultado(sorteados, vencedores)

        with lock_envio:
            conn.sendall(mensagem.encode())

HOST = ''   #host aberto para aceitar conexões de qualquer endereço (mais flexivel)
PORT = 50007

def montar_mensagem_resultado(sorteados, vencedores):
    linhas = [f'Numeros sorteados: {sorted(sorteados)}']

    for qtd_acertos, apostas in enumerate(vencedores):
        if qtd_acertos == 0 or not apostas:
            continue
        for aposta in apostas:
            acertos = sorted(set(sorteados) & aposta)
            linhas.append(f'Aposta {sorted(aposta)} acertou {qtd_acertos} numero(s): {acertos}')

    if len(linhas) == 1:
        linhas.append('nenhum vencedor nesta rodada')

    return '\n'.join(linhas) + '\n'


def atender_cliente(conn, addr, encerrar):
    horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")      #define o texto do horario: dia, mes, ano, hora, minuto, segundo
    with conn:
        print('conexão estabelecida com', addr, 'às', horario)
        msg = f'{horario} - CONECTADO!!\n' #mensagem com o horario de conexão do cliente
        conn.sendall(msg.encode())  #envia a mensagem em bytes para o cliente

        buffer = "" #aguarda bytes chegando até formar linha completa
        while True: #enquanto o cliente existir
            data = conn.recv(1024)
            if not data: break
            buffer += data.decode() #despeja o pedaço na caixa, somando o que ja havia

            while "\n" in buffer: #caso exista pelomenos uma linha completa...
                linha, buffer = buffer.split("\n", 1)   #...corta na primeira \n

                with lock:
                    if linha.startswith(':'):
                        partes = linha.split()  #separa ":txt" do valor que vem depois
                        try:
                            comando = partes[0]
                            valor = int(partes[1])  #'10' texto -> 10 numero

                            if comando == ':inicio':
                                resposta = loteria.set_min_value(valor) + '\n'
                            elif comando == ':fim':
                                resposta = loteria.set_max_value(valor) + '\n'
                            elif comando == ':qtd':
                                resposta = loteria.qtd_numeros_sorteador(valor) + '\n'
                            else:
                                resposta = 'ERRO: comando desconhecido\n'   #":" chegou, mas comando não existe

                        except (ValueError, IndexError):
                            resposta = 'ERRO: Comando mal formado\n'
                        except LoteriaException as e:   #regra do jogo violada
                            resposta = f'ERRO: {e}\n'

                    else:
                        if not linha.split():   #se for um espaço ou enter, só continua sem erro. Não faz nada
                            continue
                        try: 
                            resposta = loteria.add_ticket(linha) + '\n'
                        except AddTicketException as e:
                            resposta = f'ERRO: {e}\n'
                with lock_envio:
                    conn.sendall(resposta.encode()) #ponto de envio
                print(f'recebido: {linha} | Apostas: {loteria.fetch_tickets()}')    #olha e printa loteria.TICKETS


    horario_fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  #horario_fim deve ser diferente
    print('Conexão encerrada por', addr, 'às', horario_fim)
    encerrar.set()  #avisa t2 que o jogo acabou


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    #define opção do socket(no nivel do socket, qual opção, ligado)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     #no linux, fechar o server com ctrl+c não libera a linha. Essa parte corrige isso, permitindo checar o codigo mais rapidamente.
    s.bind((HOST, PORT))
    s.listen(5)     #de padrão vem 1, mas eu quero que mais clientes possam se conectar ao mesmo tempo, então coloco 5.

    while True:
        conn, addr = s.accept()
        encerrar = threading.Event()
        t1 = threading.Thread(target=atender_cliente, args=(conn, addr, encerrar))  #cria uma thread ("funcionario") para cada cliente que se conecta
        t2 = threading.Thread(target=ciclo_sorteio, args=(conn, encerrar))  #cria uma thread 
        t1.start() #coloca a thread ("funcionario") para trabalhar
        t2.start()  

        t1.join() #proximo accept() só depois que o cliente atual saír
        t2.join()
        
