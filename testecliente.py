import socket

HOST = '127.0.0.1'   # 127.0.0.1 = "essa mesma máquina" (localhost)
PORT = 50007          # tem que ser IGUAL à porta que você usou no servidor

# cria o socket TCP e já conecta no servidor
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))   # tenta conectar no servidor rodando localmente

    # recebe o que o servidor mandar (a MSG1) -- recv também bloqueia até chegar algo
    data = s.recv(1024)

    # converte de bytes de volta pra string legível e imprime
    print("Recebido do servidor:", data.decode())