import socket
import threading
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loteria')) #esta linha só serve para que o python leia a pasta da loteria

import loteria
from datetime import datetime
from loteria_exceptions import LoteriaException, AddTicketException


HOST = ''   #host aberto para aceitar conexões de qualquer endereço (mais flexivel)
PORT = 50007


def atender_cliente(conn, addr):
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
                conn.sendall(resposta.encode()) #ponto de envio
                print(f'recebido: {linha} | Apostas: {loteria.fetch_tickets()}')    #olha e printa loteria.TICKETS




    horario_fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  #horario_fim deve ser diferente
    print('Conexão encerrada por', addr, 'às', horario_fim)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    #define opção do socket(no nivel do socket, qual opção, ligado)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     #no linux, fechar o server com ctrl+c não libera a linha. Essa parte corrige isso, permitindo checar o codigo mais rapidamente.
    s.bind((HOST, PORT))
    s.listen(5)     #de padrão vem 1, mas eu quero que mais clientes possam se conectar ao mesmo tempo, então coloco 5.

    while True:
        conn, addr = s.accept()
        t1 = threading.Thread(target=atender_cliente, args=(conn, addr))  #cria uma thread ("funcionario") para cada cliente que se conecta
        t1.start() #coloca a thread ("funcionario") para trabalhar
        t1.join() #proximo accept() só depois que o cliente atual saír
