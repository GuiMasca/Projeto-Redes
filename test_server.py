import threading
import unittest
from unittest.mock import Mock, patch

import loteria
import server


def sessao(endereco, jogo=None):
    conn = Mock()
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)
    return {
        'conn': conn, 'addr': endereco,
        'jogo': jogo if jogo is not None else loteria.Loteria(),
        'admitido': False, 'pronto': True,
        'encerrar': threading.Event(), 'lock_envio': threading.Lock(),
    }


class IsolamentoClientesTest(unittest.TestCase):
    def setUp(self):
        patcher = patch.multiple(server, clientes_ativos=[], quantidade_clientes=0)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('builtins.print')
        patcher.start()
        self.addCleanup(patcher.stop)

    def sortear_rodada(self):
        encerrar = Mock()
        encerrar.wait.side_effect = [False, True]
        server.ciclo_sorteio(encerrar)

    def test_comandos_apostas_e_desconexao_isolados(self):
        outro = sessao('outro')
        outro['jogo'].add_ticket('1 2 3 4 5')
        cliente = sessao('cliente')
        server.clientes_ativos.extend([outro, cliente])
        cliente['conn'].recv.side_effect = [
            b':inicio 10\n:fim 20\n:qtd 2\n10 11\n:sair\n',
        ]

        server.atender_cliente(cliente, 2)

        jogo = cliente['jogo']
        self.assertEqual((jogo.min_value, jogo.max_value, jogo.qt_numbers), (10, 20, 2))
        self.assertEqual(jogo.fetch_tickets(), [{10, 11}])
        jogo_outro = outro['jogo']
        self.assertEqual((jogo_outro.min_value, jogo_outro.max_value, jogo_outro.qt_numbers), (0, 100, 5))
        self.assertEqual(jogo_outro.fetch_tickets(), [{1, 2, 3, 4, 5}])
        self.assertEqual(server.clientes_ativos, [outro])
        self.assertEqual(server.quantidade_clientes, 0)
        respostas = b''.join(c.args[0] for c in cliente['conn'].sendall.call_args_list)
        self.assertNotIn(b'ERRO', respostas)

    def test_sorteios_independentes_e_limpeza_da_rodada(self):
        a = sessao('a', loteria.Loteria(0, 10, 2))
        b = sessao('b', loteria.Loteria(20, 30, 3))
        a['jogo'].add_ticket('0 1')
        b['jogo'].add_ticket('20 21 22')
        server.clientes_ativos.extend([a, b])

        with patch.object(loteria.random, 'sample', side_effect=lambda numeros, qtd: list(numeros)[:qtd]):
            self.sortear_rodada()

        for cliente, numeros in [(a, [0, 1]), (b, [20, 21, 22])]:
            mensagem = cliente['conn'].sendall.call_args.args[0].decode()
            self.assertIn(f'Números sorteados: {numeros}', mensagem)
            self.assertIn(f'Aposta {numeros} acertou {len(numeros)}', mensagem)
            self.assertEqual(cliente['jogo'].fetch_tickets(), [])
            self.assertFalse(any(cliente['jogo'].winner_tickets))
        self.assertNotIn(b'20, 21, 22', a['conn'].sendall.call_args.args[0])
        self.assertEqual(b['jogo'].min_value, 20)
        self.assertEqual(b['jogo'].qt_numbers, 3)

    def test_cliente_sem_apostas_nao_impede_sorteio_dos_demais(self):
        vazio, apostador = sessao('vazio'), sessao('apostador')
        apostador['jogo'].add_ticket('1 2 3 4 5')
        server.clientes_ativos.extend([vazio, apostador])

        self.sortear_rodada()

        self.assertIn(b'ERRO:', vazio['conn'].sendall.call_args.args[0])
        self.assertIn('Números sorteados:', apostador['conn'].sendall.call_args.args[0].decode())
        self.assertEqual(apostador['jogo'].fetch_tickets(), [])


if __name__ == '__main__':
    unittest.main()
