import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loteria import Loteria
from loteria_exceptions import ParameterSetException, AddTicketException


@pytest.fixture
def jogo():
    return Loteria()


# --- Testes de Inicialização (__init__) ---

def test_init_defaults():
    l = Loteria()
    assert l.min_value == 0
    assert l.max_value == 100
    assert l.qt_numbers == 5
    assert l.tickets == []
    assert l.sorted_numbers == []
    assert len(l.winner_tickets) == 6
    assert all(bucket == [] for bucket in l.winner_tickets)


def test_init_negative_min_value_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        Loteria(min_value=-1)
    assert "Valores negativos" in str(exc_info.value)


def test_init_max_less_or_equal_min_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        Loteria(min_value=50, max_value=50)
    assert "mínimo não deve exceder ou ser igual" in str(exc_info.value)


def test_init_qt_numbers_zero_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        Loteria(qt_numbers=0)
    assert "maior que 0" in str(exc_info.value)


# --- Testes para set_min_value ---

def test_set_min_value_success(jogo):
    response = jogo.set_min_value(10)
    assert jogo.min_value == 10
    assert response == "MIN_VALUE atualizado: 10"


def test_set_min_value_negative_value_exception(jogo):
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.set_min_value(-5)
    assert "Valores negativos não são suportados" in str(exc_info.value)


def test_set_min_value_exceeds_max_value_exception(jogo):
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.set_min_value(105)
    assert "O valor minímo não deve exceder o valor máximo" in str(exc_info.value)


def test_set_min_value_rollback_on_qt_numbers_mismatch(jogo):
    # QT_NUMBERS=50 só cabe se o intervalo tiver pelo menos 50 números
    jogo.qtd_numeros_sorteados(50)

    with pytest.raises(ParameterSetException) as exc_info:
        jogo.set_min_value(60)  # intervalo [60,100] só tem 41 números

    assert "QT_NUMBERS" in str(exc_info.value)
    assert jogo.min_value == 0  # precisa ter revertido, não pode ter ficado em 60


# --- Testes para set_max_value ---

def test_set_max_value_success(jogo):
    response = jogo.set_max_value(50)
    assert jogo.max_value == 50
    assert response == "MAX_VALUE atualizado: 50"


def test_set_max_value_equal_to_min_value_exception(jogo):
    jogo.set_min_value(20)
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.set_max_value(20)
    assert "igual ou menor que o minímo" in str(exc_info.value)


def test_set_max_value_less_than_min_value_exception(jogo):
    jogo.set_min_value(20)
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.set_max_value(15)
    assert "igual ou menor que o minímo" in str(exc_info.value)


def test_set_max_value_rollback_on_qt_numbers_mismatch(jogo):
    jogo.qtd_numeros_sorteados(50)

    with pytest.raises(ParameterSetException) as exc_info:
        jogo.set_max_value(30)  # intervalo [0,30] só tem 31 números

    assert "QT_NUMBERS" in str(exc_info.value)
    assert jogo.max_value == 100  # precisa ter revertido, não pode ter ficado em 30


# --- Testes para qtd_numeros_sorteados ---

def test_qtd_numeros_sorteados_success(jogo):
    response = jogo.qtd_numeros_sorteados(10)
    assert jogo.qt_numbers == 10
    assert response == "QT_NUMBERS atualizado: 10"


def test_qtd_numeros_sorteados_greater_than_available_range_exception(jogo):
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.qtd_numeros_sorteados(150)
    assert "disponíveis para sorteio" in str(exc_info.value)


def test_qtd_numeros_sorteados_zero_exception(jogo):
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.qtd_numeros_sorteados(0)
    assert "maior que 0" in str(exc_info.value)


def test_qtd_numeros_sorteados_negative_exception(jogo):
    with pytest.raises(ParameterSetException) as exc_info:
        jogo.qtd_numeros_sorteados(-3)
    assert "maior que 0" in str(exc_info.value)


def test_qtd_numeros_sorteados_rebuilds_winner_tickets(jogo):
    # Garante que winner_tickets da instância é reconstruído
    jogo.qtd_numeros_sorteados(8)
    assert len(jogo.winner_tickets) == 9  # índices 0..8
    assert all(bucket == [] for bucket in jogo.winner_tickets)


# --- Testes para add_ticket ---

def test_add_ticket_success(jogo):
    response = jogo.add_ticket("1 2 3 4 5")
    assert "foi adicionada com sucesso" in response
    assert {1, 2, 3, 4, 5} in jogo.tickets


def test_add_ticket_empty_string_exception(jogo):
    with pytest.raises(AddTicketException) as exc_info:
        jogo.add_ticket("   ")
    assert "A aposta não deve estar vazia" in str(exc_info.value)


def test_add_ticket_non_numeric_values_exception(jogo):
    with pytest.raises(AddTicketException) as exc_info:
        jogo.add_ticket("1 2 tres 4 5")
    assert "valores numéricos" in str(exc_info.value)


def test_add_ticket_numbers_out_of_range_exception(jogo):
    with pytest.raises(AddTicketException) as exc_info:
        jogo.add_ticket("0 50 101 2 3")
    assert "intervalo de" in str(exc_info.value)


def test_add_ticket_duplicate_numbers_exception(jogo):
    with pytest.raises(AddTicketException) as exc_info:
        jogo.add_ticket("5 5 10 10 20")
    assert "números repetidos" in str(exc_info.value)


def test_add_ticket_wrong_quantity_no_duplicates_exception(jogo):
    with pytest.raises(AddTicketException) as exc_info:
        jogo.add_ticket("1 2 3")
    assert f"deve conter {jogo.qt_numbers} números" in str(exc_info.value)


# --- Testes para reset_tickets ---

def test_reset_tickets(jogo):
    jogo.add_ticket("1 2 3 4 5")
    assert len(jogo.tickets) == 1

    jogo.reset_tickets()
    assert jogo.tickets == []


# --- Testes para fetch_tickets ---

def test_fetch_tickets_success(jogo):
    jogo.add_ticket("0 1 2 3 4")
    tickets = jogo.fetch_tickets()
    assert len(tickets) == 1
    assert tickets[0] == {0, 1, 2, 3, 4}


def test_fetch_tickets_returns_copy(jogo):
    jogo.add_ticket("0 1 2 3 4")
    tickets = jogo.fetch_tickets()
    tickets.clear()
    assert len(jogo.tickets) == 1


# --- Testes para realizar_sorteio ---

def test_realizar_sorteio_with_matches(jogo, monkeypatch):
    monkeypatch.setattr("random.sample", lambda range_val, k: [0, 1, 2, 3, 4])

    jogo.add_ticket("0 1 2 3 4")  # 5 acertos
    jogo.add_ticket("0 1 2 8 9")  # 3 acertos

    sorteados, vencedores = jogo.realizar_sorteio()

    assert set(sorteados) == {0, 1, 2, 3, 4}
    assert set(jogo.sorted_numbers) == {0, 1, 2, 3, 4}
    assert {0, 1, 2, 3, 4} in vencedores[5]
    assert {0, 1, 2, 8, 9} in vencedores[3]


def test_realizar_sorteio_no_matches(jogo, monkeypatch):
    monkeypatch.setattr("random.sample", lambda range_val, k: [0, 1, 2, 3, 4])

    jogo.add_ticket("50 51 52 53 54")  # Nenhum acerto

    sorteados, vencedores = jogo.realizar_sorteio()

    for qt_acertos in range(1, jogo.qt_numbers + 1):
        assert vencedores[qt_acertos] == []


def test_realizar_sorteio_sem_apostas(jogo, monkeypatch):
    monkeypatch.setattr("random.sample", lambda range_val, k: [0, 1, 2, 3, 4])

    sorteados, vencedores = jogo.realizar_sorteio()
    assert set(sorteados) == {0, 1, 2, 3, 4}
    assert all(bucket == [] for bucket in vencedores)


def test_realizar_sorteio_returns_references(jogo, monkeypatch):
    monkeypatch.setattr("random.sample", lambda range_val, k: [0, 1, 2, 3, 4])

    jogo.add_ticket("0 1 2 3 4")
    sorteados, vencedores = jogo.realizar_sorteio()

    assert sorteados is jogo.sorted_numbers
    assert vencedores is jogo.winner_tickets


def test_realizar_sorteio_does_not_clear_tickets(jogo, monkeypatch):
    monkeypatch.setattr("random.sample", lambda range_val, k: [0, 1, 2, 3, 4])

    jogo.add_ticket("0 1 2 3 4")
    jogo.realizar_sorteio()

    assert len(jogo.tickets) == 1


# --- Teste de Isolamento entre Instâncias ---

def test_instancias_independentes():
    jogo1 = Loteria()
    jogo2 = Loteria()

    jogo1.set_min_value(10)
    jogo1.qtd_numeros_sorteados(6)
    jogo1.add_ticket("10 11 12 13 14 15")

    assert jogo2.min_value == 0
    assert jogo2.max_value == 100
    assert jogo2.qt_numbers == 5
    assert len(jogo2.tickets) == 0