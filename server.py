import socket

HOST = 'localhost'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
server.listen(1)

print(f"Servidor esperando conexão em {HOST}:{PORT}...")

conn, addr = server.accept()

print(f"Cliente conectado: {addr}")

conn.sendall("Olá! Você está conectado ao servidor.".encode())

while True:
    data = conn.recv(1024)

    if not data:
        break

    mensagem = data.decode()

    print("Cliente:", mensagem)

    if mensagem.lower() == "exit":
        break

    resposta = "Servidor recebeu: " + mensagem

    conn.sendall(resposta.encode())

conn.close()
server.close()

print("Servidor encerrado.")