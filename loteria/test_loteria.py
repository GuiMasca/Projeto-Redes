import pytest
import loteria
from loteria_exceptions import (
    LoteriaException,
    ParameterSetException,
    AddTicketException
)

@pytest.fixture(autouse=True)
def reset_global_variables():
    loteria.MIN_VALUE = 0
    loteria.MAX_VALUE = 100
    loteria.QT_NUMBERS = 5
    loteria.TICKETS = []

# --- Testes para set_min_value ---

def test_set_min_value_success():
    response = loteria.set_min_value(10)
    assert loteria.MIN_VALUE == 10
    assert response == "MIN_VALUE atualizado: 10"

def test_set_min_value_negative_value_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_min_value(-5)
    assert "Valores negativos não suportados" in str(exc_info.value)

# --- Testes para set_max_value ---

def test_set_max_value_success():
    response = loteria.set_max_value(50)
    assert loteria.MAX_VALUE == 50
    assert response == "MAX_VALUE atualizado: 50"

def test_set_max_value_equal_to_min_value_exception():
    loteria.set_min_value(20)
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_max_value(20)
    assert "não pode ser menor ou igual" in str(exc_info.value)

def test_set_max_value_less_than_min_value_exception():
    loteria.set_min_value(20)
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.set_max_value(15)
    assert "não pode ser menor ou igual" in str(exc_info.value)

# --- Testes para qtd_numeros_sorteador ---

def test_qtd_numeros_sorteador_success():
    response = loteria.qtd_numeros_sorteador(10)
    assert loteria.QT_NUMBERS == 10
    assert response == "QT_NUMBERS atualizado: 10"

def test_qtd_numeros_sorteador_greater_than_max_value_exception():
    with pytest.raises(ParameterSetException) as exc_info:
        loteria.qtd_numeros_sorteador(150)
    assert "deve ser menor que o valor máximo" in str(exc_info.value)

# --- Testes para add_ticket ---

def test_add_ticket_success():
    response = loteria.add_ticket("1 2 3 4 5")
    assert response == "Aposta adicionada com sucesso"
    assert {1, 2, 3, 4, 5} in loteria.TICKETS

def test_add_ticket_empty_string_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("   ")
    assert "A aposta não deve estar vazia" in str(exc_info.value)

def test_add_ticket_non_numeric_values_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("1 2 tres 4 5")
    assert "A aposta deve conter somente valores" in str(exc_info.value)

def test_add_ticket_numbers_out_of_range_exception():
    with pytest.raises(AddTicketException) as exc_info:
        loteria.add_ticket("0 50 101")
    assert "Números não cobridos pela aposta foram inseridos" in str(exc_info.value)

def test_add_ticket_handles_duplicate_numbers_correctly():
    loteria.add_ticket("5 5 10 10 20")
    assert loteria.TICKETS[0] == {5, 10, 20}