import socket
from datetime import datetime

horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")      #define o texto do horario: dia, mes, ano, hora, minuto, segundo

HOST = ''   #host aberto para aceitar conexões de qualquer endereço (mais flexivel) 
PORT = 50007              
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    #define opção do socket(no nivel do socket, qual opção, ligado)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     #no linux, fechar o server com ctrl+c não libera a linha. Essa parte corrige isso, permitindo checar o codigo mais rapidamente.
    s.bind((HOST, PORT))
    s.listen(5)     #de padrão vem 1, mas eu quero que mais clientes possam se conectar ao mesmo tempo, então coloco 5.

    while True:     #permite que o servidor "viva para sempre"
        conn, addr = s.accept()  #aceita a conexão do cliente, agora dentro do loop
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")      #define o texto do horario: dia, mes, ano, hora, minuto, segundo
        with conn:
            print('conexão estabelecida com', addr, 'ás', horario)
            msg = f'{horario} - CONECTADO!!\n' #mensagem com o horario de conexão do cliente
            conn.sendall(msg.encode())  #envia a mensagem em bytes para o cliente

            while True:
                data = conn.recv(1024)
                if not data: break
                conn.sendall(data)
        print('Conexão encerrada por', addr, 'ás', horario)