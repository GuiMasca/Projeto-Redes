import pytest
import loteria
from loteria_exceptions import LoteriaException

@pytest.fixture(autouse=True)
def reset_global_variables() :
	loteria.MIN_VALUE = 0
	loteria.MAX_VALUE = 100
	loteira.QT_NUMBERS = 5

def test_set_min_value_success() :
	response = loteria.set_min_value(10)
	assert loteria.MIN_VALUE == 10
	assert resposta == "MIN_VALUE atualizado: 10"

def test_set_min_value_negative_value_exception() :
	with pytest.raises(LoteriaException) as exc_info :
		loteria.set_min_value(-5)
	assert "Valores negativos não suportados" in str(exc_info.value)

def test_set_max_value_success() :
	response = loteria.set_min_value(50)
	assert loteria.MIN_VALUE == 50
	assert resposta == "MIN_VALUE atualizado: 50"

def test_set_max_value_less_than_or_equal_to_min_value_exception() :
	loteria.set_min_value(20)

	with pytest.raises(LoteriaException):
		loteria.set_max_value(20)

	with pytest.raises(LoteriaException):
		loteria.set_max_value(15)

