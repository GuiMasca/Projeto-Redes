import pytest
import loteria
from loteria_exceptions import ParameterSetException, AddTicketException

@pytest.fixture(autouse=True)
def reset_global_variables():
    loteria.MIN_VALUE = 0
    loteria.MAX_VALUE = 100
    loteria.QT_NUMBERS = 5
    loteria.TICKETS = []
    loteria.SORTED_NUMBERS = []
    loteria.WINNER_TICKETS = loteria._build_empty_winner_tickets()

# --- Testes para set_min_value ---

def test_set_min_value_success():
    response = loteria.set_min_value(10)
    assert loteria.MIN_VALUE == 10
    assert response == "MIN_VALUE atualizado: 10"

def test_set_min_value_negative_value_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_min_value(-5)
    assert "Valores negativos não são suportados" in str(exc_info.value)

def test_set_min_value_exceeds_max_value_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_min_value(105)
    assert "O valor minímo não deve exceder o valor máximo" in str(exc_info.value)

def test_set_min_value_rollback_on_qt_numbers_mismatch():
    # QT_NUMBERS=50 só cabe se o intervalo tiver pelo menos 50 números
    loteria.qtd_numeros_sorteador(50)

    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_min_value(60)  # intervalo [60,100] só tem 41 números

    assert "QT_NUMBERS" in str(exc_info.value)
    assert loteria.MIN_VALUE == 0  # precisa ter revertido, não pode ter ficado em 60

# --- Testes para set_max_value ---

def test_set_max_value_success():
    response = loteria.set_max_value(50)
    assert loteria.MAX_VALUE == 50
    assert response == "MAX_VALUE atualizado: 50"

def test_set_max_value_equal_to_min_value_exception():
    loteria.set_min_value(20)
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_max_value(20)
    assert "igual ou menor que o minímo" in str(exc_info.value)

def test_set_max_value_less_than_min_value_exception():
    loteria.set_min_value(20)
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_max_value(15)
    assert "igual ou menor que o minímo" in str(exc_info.value)

def test_set_max_value_rollback_on_qt_numbers_mismatch():
    loteria.qtd_numeros_sorteador(50)

    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_max_value(30)  # intervalo [0,30] só tem 31 números

    assert "QT_NUMBERS" in str(exc_info.value)
    assert loteria.MAX_VALUE == 100  # precisa ter revertido, não pode ter ficado em 30

# --- Testes para qtd_numeros_sorteador ---

def test_qtd_numeros_sorteador_success():
    response = loteria.qtd_numeros_sorteador(10)
    assert loteria.QT_NUMBERS == 10
    assert response == "QT_NUMBERS atualizado: 10"

def test_qtd_numeros_sorteador_greater_than_available_range_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.qtd_numeros_sorteador(150)
    assert "disponíveis para sorteio" in str(exc_info.value)

def test_qtd_numeros_sorteador_zero_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.qtd_numeros_sorteador(0)
    assert "maior que 0" in str(exc_info.value)

def test_qtd_numeros_sorteador_negative_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.qtd_numeros_sorteador(-3)
    assert "maior que 0" in str(exc_info.value)

def test_qtd_numeros_sorteador_rebuilds_winner_tickets():
    # Teste de regressão: garante que WINNER_TICKETS global é
    # realmente reconstruído (bug anterior: faltava "global WINNER_TICKETS")
    loteria.qtd_numeros_sorteador(8)
    assert len(loteria.WINNER_TICKETS) == 9  # índices 0..8
    assert all(bucket == [] for bucket in loteria.WINNER_TICKETS)

# --- Testes para add_ticket ---

def test_add_ticket_success():
    response = loteria.add_ticket("1 2 3 4 5")
    assert "foi adicionada com sucesso" in response
    assert {1, 2, 3, 4, 5} in loteria.TICKETS

def test_add_ticket_empty_string_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("   ")
    assert "A aposta não deve estar vazia" in str(exc_info.value)

def test_add_ticket_non_numeric_values_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("1 2 tres 4 5")
    assert "valores numéricos" in str(exc_info.value)

def test_add_ticket_numbers_out_of_range_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("0 50 101 2 3")
    assert "intervalo de" in str(exc_info.value)

def test_add_ticket_duplicate_numbers_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("5 5 10 10 20")
    assert "números repetidos" in str(exc_info.value)

def test_add_ticket_wrong_quantity_no_duplicates_exception():
    # Sem duplicados, mas com menos números do que QT_NUMBERS exige
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("1 2 3")
    assert f"deve conter {loteria.QT_NUMBERS} números" in str(exc_info.value)

# --- Testes para reset_tickets ---

def test_reset_tickets():
    loteria.add_ticket("1 2 3 4 5")
    assert len(loteria.TICKETS) == 1

    loteria.reset_tickets()
    assert loteria.TICKETS == []

# --- Testes para fetch_tickets ---

def test_fetch_tickets_success():
    loteria.add_ticket("0 1 2 3 4")
    tickets = loteria.fetch_tickets()
    assert len(tickets) == 1
    assert tickets[0] == {0, 1, 2, 3, 4}

def test_fetch_tickets_returns_copy():
    loteria.add_ticket("0 1 2 3 4")
    tickets = loteria.fetch_tickets()
    tickets.clear()
    assert len(loteria.TICKETS) == 1

# --- Testes para temp_numbers_sort ---

def test_temp_numbers_sort_with_matches(monkeypatch):
    # Fixa o retorno do sorteio aleatório para garantir reprodutibilidade
    monkeypatch.setattr(loteria.random, "sample", lambda range_val, k: [0, 1, 2, 3, 4])

    loteria.add_ticket("0 1 2 3 4")  # 5 acertos
    loteria.add_ticket("0 1 2 8 9")  # 3 acertos

    loteria.temp_numbers_sort()

    assert set(loteria.SORTED_NUMBERS) == {0, 1, 2, 3, 4}
    assert {0, 1, 2, 3, 4} in loteria.WINNER_TICKETS[5]
    assert {0, 1, 2, 8, 9} in loteria.WINNER_TICKETS[3]

def test_temp_numbers_sort_no_matches(monkeypatch):
    monkeypatch.setattr(loteria.random, "sample", lambda range_val, k: [0, 1, 2, 3, 4])

    loteria.add_ticket("50 51 52 53 54")  # Nenhum acerto

    loteria.temp_numbers_sort()

    for qt_acertos in range(1, loteria.QT_NUMBERS + 1):
        assert loteria.WINNER_TICKETS[qt_acertos] == []

def test_temp_numbers_sort_returns_winner_tickets(monkeypatch):
    # Teste de regressão: garante que a função retorna WINNER_TICKETS
    # (bug anterior: faltava o "return" no final de temp_numbers_sort)
    monkeypatch.setattr(loteria.random, "sample", lambda range_val, k: [0, 1, 2, 3, 4])

    loteria.add_ticket("0 1 2 3 4")
    result = loteria.temp_numbers_sort()

    assert result is loteria.WINNER_TICKETS

def test_temp_numbers_sort_does_not_clear_tickets(monkeypatch):
    # Decisão de design: quem decide quando zerar as apostas é o servidor,
    # não o sorteio em si.
    monkeypatch.setattr(loteria.random, "sample", lambda range_val, k: [0, 1, 2, 3, 4])

    loteria.add_ticket("0 1 2 3 4")
    loteria.temp_numbers_sort()

    assert len(loteria.TICKETS) == 1