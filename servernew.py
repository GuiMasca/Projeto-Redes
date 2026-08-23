import socket

HOST = ''   #host aberto para aceitar conexões de qualquer endereço (mais flexivel) 
PORT = 50007              
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    
    #define opção do socket(no nivel do socket, qual opção, ligado)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     #no linux, fechar o server com ctrl+c não libera a linha. Essa parte corrige isso, permitindo checar o codigo mais rapidamente.
    s.bind((HOST, PORT))
    s.listen(5)     #de padrão vem 1, mas eu quero que mais clientes possam se conectar ao mesmo tempo, então coloco 5.
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data: break
            conn.sendall(data)