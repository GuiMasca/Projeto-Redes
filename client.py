# Echo client program
import socket

HOST = ''    # The remote host
PORT = 50010              # The same port as used by the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    data = s.recv(1024)

print(data.decode('utf-8'))