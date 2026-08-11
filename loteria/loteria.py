# preciso receber:
#	o menor valor a ser sorteado (vide, início)
#	o maior valor a ser sorteado (vide, fim)
#	a quantidade dos números a serem tirados
#	os números que serão apostados (na forma: 1 2 3 4 ... 23 34 56, com os números separados por espaço)

from loteria_exceptions import LoteriaException

MIN_VALUE = 0
MAX_VALUE = 100
QT_NUMBERS = 5
TICKETS = []

def set_min_value (new_value) :
	global MIN_VALUE

	if (new_value < 0) :
		raise LoteriaException("Valores negativos não suportados")
	else :
		MIN_VALUE = new_value
		return f"MIN_VALUE atualizado: {MIN_VALUE}"

def set_max_value (new_value) :
	global MAX_VALUE

	if (new_value <= MIN_VALUE) :
		raise LoteriaException("O valor máximo não pode ser menor ou igual que o valor minímo")
	else :
		MAX_VALUE = new_value
		return f"MAX_VALUE atualizado: {MAX_VALUE}"

def qtd_numeros_sorteador (qtd) :
	global QT_NUMBERS

	if (qtd > MAX_VALUE) :
		raise LoteriaException("A quantidade de números sorteados deve ser menor que o valor máximo")
	else :
		QT_NUMBERS = qtd
		return f"QT_NUMBERS atualizado: {QT_NUMBERS}"

def add_ticket(numbers_input) :
	global TICKETS

	if (not numbers_input or not str(numbers_input).strip()) :
		raise LoteriaException("A aposta não deve estar vazia")

	try :
		parsed_numbers = [int(n) for n in numbers_input.split()]
	except ValueError:
		raise LoteriaException("A aposta deve conter somente valores")

	parsed_numbers = set(parsed_numbers)
	available_numbers_set = set(range(MIN_VALUE, MAX_VALUE + 1))

	if (not parsed_numbers.issubset(available_numbers_set)) :
		raise LoteriaException("Números não cobridos pela aposta foram inseridos")

	TICKETS.append(parsed_numbers)

	return f"Aposta adicionada com sucesso"