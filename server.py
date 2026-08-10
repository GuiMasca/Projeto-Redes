# Echo server program
import socket
from datetime import datetime

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50010              # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = f'<{now}>:CONECTADO!!'.encode('utf-8')
        conn.sendall(data)