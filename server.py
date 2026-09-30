import socket
import sys
import threading
from datetime import datetime

import loteria
from loteria import AddTicketException, LoteriaException

lock = threading.Lock()
quantidade_clientes = 0
clientes_ativos = []  # Sessões e referências das threads, inclusive durante a admissão.
jogo = loteria.Loteria()  # Configuração e sorteio comuns a todos os clientes.
INTERVALO_SORTEIO = 60


def interromper_cliente(cliente):
    cliente['encerrar'].set()
    try:
        cliente['conn'].shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def ciclo_sorteio(encerrar):
    # Um único relógio: todos participam da mesma rodada.
    while not encerrar.wait(INTERVALO_SORTEIO):
        with lock:
            participantes = [c for c in clientes_ativos if c['pronto'] and not c['encerrar'].is_set()]
            if not participantes:
                continue
            try:
                sorteados, vencedores = jogo.realizar_sorteio()
            except LoteriaException as e:
                # A loteria atual recusa sorteios sem apostas; mantém o ciclo vivo.
                mensagem = f'ERRO: {e}\n'
                print(f'Sorteio não realizado: {e}')
                envios = [(c, mensagem) for c in participantes]
            else:
                mensagem = montar_mensagem_resultado(sorteados, vencedores)
                print(f'Sorteio realizado:\n{mensagem}', end='')
                envios = []
                for cliente in participantes:
                    # Identidade distingue apostas iguais feitas por clientes diferentes.
                    apostas_cliente = {id(aposta) for aposta in cliente['apostas']}
                    vencedores_cliente = [
                        [aposta for aposta in grupo if id(aposta) in apostas_cliente]
                        for grupo in vencedores
                    ]
                    envios.append((cliente, montar_mensagem_resultado(sorteados, vencedores_cliente)))
                    cliente['apostas'].clear()
                jogo.reset_tickets()
                jogo.winner_tickets = [[] for _ in range(jogo.qt_numbers + 1)]

        for cliente, mensagem in envios:
            with cliente['lock_envio']:
                if cliente['encerrar'].is_set():
                    continue
                try:
                    cliente['conn'].sendall(mensagem.encode())
                except OSError:
                    interromper_cliente(cliente)

HOST = ''   #host aberto para aceitar conexões de qualquer endereço (mais flexivel)
PORT = 50007

def montar_mensagem_resultado(sorteados, vencedores):
    linhas = [f'Números sorteados: {sorted(sorteados)}']

    for qtd_acertos, apostas in enumerate(vencedores):
        if qtd_acertos == 0 or not apostas:
            continue
        for aposta in apostas:
            acertos = sorted(set(sorteados) & aposta)
            linhas.append(f'Aposta {sorted(aposta)} acertou {qtd_acertos} numero(s): {acertos}')

    if len(linhas) == 1:
        linhas.append('nenhum vencedor nesta rodada')

    return '\n'.join(linhas) + '\n'


def atender_cliente(cliente, limite_clientes):
    conn, addr = cliente['conn'], cliente['addr']
    global quantidade_clientes
    horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")      #define o texto do horario: dia, mes, ano, hora, minuto, segundo

    try:
        with conn:
            # A própria working thread reserva a vaga de forma atômica.
            with lock:
                if quantidade_clientes < limite_clientes:
                    quantidade_clientes += 1
                    cliente['admitido'] = True
            if not cliente['admitido']:
                conn.sendall('Limite de clientes excedido. A conexão será encerrada\n'.encode())
                return

            with cliente['lock_envio']:
                conn.sendall(f'{horario}: CONECTADO!!\n'.encode())
            with lock:
                cliente['pronto'] = True
            print('conexão estabelecida com', addr, 'às', horario)
            buffer = "" #aguarda bytes chegando até formar linha completa
            conectado = True

            while conectado: #enquanto o cliente existir
                try:
                    data = conn.recv(1024)   #espera uma mensagem do cliente
                except OSError:              #conexao caiu de forma abrupta (reset de rede): mesmo destino do fim normal
                    break
                if not data: break           #recv vazio = cliente fechou do jeito limpo
                buffer += data.decode() #despeja o pedaço na caixa, somando o que ja havia

                while "\n" in buffer: #caso exista pelomenos uma linha completa...
                    linha, buffer = buffer.split("\n", 1)   #...corta na primeira \n
                    linha_limpa = linha.strip()

                    with lock:
                        if (linha_limpa == ":sair") :
                            resposta = "Desconectado com sucesso\n"
                            conectado = False
                            cliente['encerrar'].set()

                        elif linha.startswith(':'):
                            partes = linha.split()  #separa ":txt" do valor que vem depois
                            try:
                                comando = partes[0]
                                valor = int(partes[1])  #'10' texto -> 10 numero

                                if comando == ':inicio':
                                    resposta = jogo.set_min_value(valor) + '\n'
                                elif comando == ':fim':
                                    resposta = jogo.set_max_value(valor) + '\n'
                                elif comando == ':qtd':
                                    resposta = jogo.qtd_numeros_sorteados(valor) + '\n'
                                else:
                                    resposta = 'ERRO: comando desconhecido\n'   #":" chegou, mas comando não existe

                            except (ValueError, IndexError):
                                resposta = 'ERRO: Comando mal formado\n'
                            except LoteriaException as e:   #regra do jogo violada
                                resposta = f'ERRO: {e}\n'

                        else:
                            if not linha_limpa :
                                continue

                            try:
                                resposta = jogo.add_ticket(linha_limpa) + '\n'
                                cliente['apostas'].append(jogo.tickets[-1])
                            except AddTicketException as e:
                                resposta = f'ERRO:{e}\n'

                    with cliente['lock_envio']:
                        conn.sendall(resposta.encode()) #ponto de envio

                    if not conectado:
                        break
                    
                    with lock:
                        print(f'recebido: {linha} | Apostas: {jogo.fetch_tickets()} | Cliente: {addr}')

    except (OSError, UnicodeDecodeError):
        pass
    finally:
        interromper_cliente(cliente)
        with lock:
            if cliente['admitido']:
                quantidade_clientes -= 1
            # Remove somente os bilhetes desta conexão, preservando os demais.
            apostas_cliente = {id(aposta) for aposta in cliente['apostas']}
            jogo.tickets[:] = [a for a in jogo.tickets if id(a) not in apostas_cliente]
            cliente['apostas'].clear()
            clientes_ativos.remove(cliente)
        horario_fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print('Conexão encerrada por', addr, 'às', horario_fim)


def executar_servidor(limite_clientes):
    encerrar = threading.Event()
    t2 = threading.Thread(target=ciclo_sorteio, args=(encerrar,))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)  # Fila de conexões pendentes, não limite de clientes.
        t2.start()
        try:
            while True:
                conn, addr = s.accept()
                cliente = {
                    'conn': conn, 'addr': addr, 'apostas': [], 'admitido': False, 'pronto': False,
                    'encerrar': threading.Event(), 'lock_envio': threading.Lock(),
                }
                t1 = threading.Thread(target=atender_cliente, args=(cliente, limite_clientes))
                cliente['thread'] = t1
                with lock:
                    clientes_ativos.append(cliente)
                try:
                    t1.start()
                except Exception:
                    with lock:
                        clientes_ativos.remove(cliente)
                    conn.close()
                    raise
        except KeyboardInterrupt:
            print('\nServidor encerrado pelo usuario.')
        finally:
            encerrar.set()
            with lock:
                restantes = list(clientes_ativos)
            for cliente in restantes:
                interromper_cliente(cliente)
            for cliente in restantes:
                cliente['thread'].join()
            t2.join()


def main():
    uso = f'Uso: python3 {sys.argv[0]} <limite_clientes> (inteiro maior que zero)'
    if len(sys.argv) != 2:
        sys.exit(uso)
    try:
        limite_clientes = int(sys.argv[1])
    except ValueError:
        sys.exit(uso)
    if limite_clientes <= 0:
        sys.exit(uso)
    executar_servidor(limite_clientes)


if __name__ == '__main__':
    main()
