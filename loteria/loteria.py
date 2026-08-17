# preciso receber:
#	o menor valor a ser sorteado (vide, início)
#	o maior valor a ser sorteado (vide, fim)
#	a quantidade dos números a serem tirados
#	os números que serão apostados (na forma: 1 2 3 4 ... 23 34 56, com os números separados por espaço)

import random

from loteria_exceptions import LoteriaException, ParameterSetException, AddTicketException

MIN_VALUE = 0
MAX_VALUE = 100
QT_NUMBERS = 5
TICKETS = []
SORTED_NUMBERS = []
WINNER_TICKETS = []

def set_min_value (new_value) :
	global MIN_VALUE

	if (new_value < 0) :
		raise ParameterSetException("Valores negativos não suportados")
	else :
		MIN_VALUE = new_value
		return f"MIN_VALUE atualizado: {MIN_VALUE}"

def set_max_value (new_value) :
	global MAX_VALUE

	if (new_value <= MIN_VALUE) :
		raise ParameterSetException("O valor máximo não pode ser menor ou igual que o valor minímo")
	else :
		MAX_VALUE = new_value
		return f"MAX_VALUE atualizado: {MAX_VALUE}"

def qtd_numeros_sorteador (qtd) :
	global QT_NUMBERS

	if (qtd > MAX_VALUE) :
		raise ParameterSetException("A quantidade de números sorteados deve ser menor que o valor máximo")
	else :
		QT_NUMBERS = qtd
		return f"QT_NUMBERS atualizado: {QT_NUMBERS}"

def add_ticket(numbers_input) :
	global TICKETS

	if (not numbers_input or not str(numbers_input).strip()) :
		raise AddTicketException("A aposta não deve estar vazia")

	try :
		parsed_numbers = [int(n) for n in numbers_input.split()]
	except ValueError:
		raise AddTicketException("A aposta deve conter somente valores")

	parsed_numbers = set(parsed_numbers)

	if (len(parsed_numbers) != QT_NUMBERS) :
		raise AddTicketException("Quantidade de números únicos inválida")
	
	available_numbers_set = set(range(MIN_VALUE, MAX_VALUE + 1))

	if (not parsed_numbers.issubset(available_numbers_set)) :
		raise AddTicketException("Números não cobridos pela aposta foram inseridos")

	TICKETS.append(parsed_numbers)

	return f"Aposta adicionada com sucesso"

# funções temporárias

def temp_numbers_sort() :
	global SORTED_NUMBERS, WINNER_TICKETS

	SORTED_NUMBERS = []
	WINNER_TICKETS = {i: [] for i in range(1, QT_NUMBERS + 1)}

	random.seed()

	# sampled = random.sample(range(MIN_VALUE, MAX_VALUE + 1), QT_NUMBERS)
	# for num in sampled :
	#	SORTED_NUMBERS.append(num)

	for i in range(MIN_VALUE, MIN_VALUE + QT_NUMBERS) :
		SORTED_NUMBERS.append(i)

	SORTED_NUMBERS = set(SORTED_NUMBERS)

	for ticket in TICKETS :
		qt_matches = len(SORTED_NUMBERS & ticket)
		if (qt_matches != 0) : WINNER_TICKETS[qt_matches].append(ticket)
		
def fetch_tickets() :
	return TICKETS.copy()