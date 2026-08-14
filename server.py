import socket
from datetime import datetime


HOST = ''
PORT = 50007

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)

    print("Servidor aguardando conexão...")

    conn, addr = s.accept()

    with conn:
        print("Conexão estabelecida com:", addr)
        print("/n/n")

        horario = datetime.now().strftime("%d-%m-%y %H:%M:%S")

        msg1 = f"{horario} - CONECTADO!! /n/n"

        conn.sendall(msg1.encode())

        print("Mensagem enviada", msg1)