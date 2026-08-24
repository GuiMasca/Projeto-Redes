# preciso receber:
#	o menor valor a ser sorteado (vide, início)
#	o maior valor a ser sorteado (vide, fim)
#	a quantidade dos números a serem tirados
#	os números que serão apostados (na forma: 1 2 3 4 ... 23 34 56, com os números separados por espaço)

import random

from loteria_exceptions import LoteriaException, ParameterSetException, AddTicketException

# funções auxiliares
def _build_empty_winner_tickets() :
    return [[] for _ in range(QT_NUMBERS + 1)]

def _range_of_available_numbers() :
    return MAX_VALUE - MIN_VALUE + 1

def _check_qt_numbers_fits_range() :
    if QT_NUMBERS > _range_of_available_numbers() :
        raise ParameterSetException(f"QT_NUMBERS | {QT_NUMBERS} deve ser menor que a quantidade de números disponíveis no intervalo entre {MIN_VALUE} ~ {MAX_VALUE}")

# parâmetros globais
MIN_VALUE = 0
MAX_VALUE = 100
QT_NUMBERS = 5
TICKETS = []
SORTED_NUMBERS = []
WINNER_TICKETS = _build_empty_winner_tickets()

# funções para setar parâmetros
def set_min_value (new_value) :
	global MIN_VALUE

	if (new_value < 0) :
		raise ParameterSetException("Valores negativos não são suportados")
	
	if (new_value >= MAX_VALUE) :
		raise ParameterSetException("O valor minímo não deve exceder o valor máximo")

	old_value = MIN_VALUE
	MIN_VALUE = new_value
 
	try:
		_check_qt_numbers_fits_range()
	except ParameterSetException :
		MIN_VALUE = old_value
		raise

	return f"MIN_VALUE atualizado: {MIN_VALUE}"

def set_max_value (new_value) :
	global MAX_VALUE

	if (new_value <= MIN_VALUE) :
		raise ParameterSetException("O valor máximo não pode ser igual ou menor que o minímo")

	old_value = MAX_VALUE
	MAX_VALUE = new_value

	try :
		_check_qt_numbers_fits_range()
	except ParameterSetException :
		MAX_VALUE = old_value
		raise

	return f"MAX_VALUE atualizado: {MAX_VALUE}"


def qtd_numeros_sorteador (qtd) :
	global QT_NUMBERS, WINNER_TICKETS

	if (qtd < 1) :
		raise ParameterSetException("A quantidade de números a serem sorteados deve ser maior que 0")

	if (qtd > _range_of_available_numbers()) :
		raise ParameterSetException("A quantidade de números a serem sorteados deve ser menor que a quantidade de números disponíveis para sorteio")

	QT_NUMBERS = qtd
	WINNER_TICKETS = _build_empty_winner_tickets()

	return f"QT_NUMBERS atualizado: {QT_NUMBERS}"

# sorteio
def add_ticket(numbers_input) :
	global TICKETS

	if (not numbers_input or not str(numbers_input).strip()) :
		raise AddTicketException("A aposta não deve estar vazia")

	try :
		parsed_numbers = [int(n) for n in numbers_input.split()]
	except ValueError :
		raise AddTicketException("A aposta deve conter somente valores numéricos")

	qt_informados = len(parsed_numbers)
	parsed_numbers = set(parsed_numbers)

	if (qt_informados != len(parsed_numbers)) :
		raise AddTicketException(f"A aposta contém números repetidos (a aposta deve conter {QT_NUMBERS} números únicos)")

	if (len(parsed_numbers) != QT_NUMBERS) :
		raise AddTicketException(f"A aposta deve conter {QT_NUMBERS} números")

	available_numbers_set = set(range(MIN_VALUE, MAX_VALUE + 1))

	if (not parsed_numbers.issubset(available_numbers_set)) :
		raise AddTicketException(f"A aposta deve conter somente valores no intervalo de {MIN_VALUE} a {MAX_VALUE}")

	TICKETS.append(parsed_numbers)

	return f"A aposta {parsed_numbers} foi adicionada com sucesso"

def reset_tickets() :
	TICKETS.clear()

def reset_all() :
	"""Restaura todos os parâmetros globais para os valores padrão."""
	global MIN_VALUE, MAX_VALUE, QT_NUMBERS, WINNER_TICKETS

	MIN_VALUE = 0
	MAX_VALUE = 100
	QT_NUMBERS = 5
	TICKETS.clear()
	SORTED_NUMBERS.clear()
	WINNER_TICKETS = _build_empty_winner_tickets()

def fetch_tickets() :
	return TICKETS.copy()

# funções temporárias

def temp_numbers_sort() :
	global SORTED_NUMBERS, WINNER_TICKETS

	WINNER_TICKETS = _build_empty_winner_tickets()
	SORTED_NUMBERS = random.sample(range(MIN_VALUE, MAX_VALUE + 1), QT_NUMBERS)

	sorted_numbers_set = set(SORTED_NUMBERS)

	for ticket in TICKETS :
		qt_matches = len(sorted_numbers_set & ticket)

		if (qt_matches != 0) :
			WINNER_TICKETS[qt_matches].append(ticket)

	return WINNER_TICKETS