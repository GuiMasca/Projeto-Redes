# preciso receber:
#	o menor valor a ser sorteado (vide, início)
#	o maior valor a ser sorteado (vide, fim)
#	a quantidade dos números a serem tirados
#	os números que serão apostados (na forma: 1 2 3 4 ... 23 34 56, com os números separados por espaço)

import random

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loteria'))
from loteria_exceptions import LoteriaException, ParameterSetException, AddTicketException

class Loteria:
	#construtor
	def __init__(self, min_value=0, max_value=100, qt_numbers=5):
		if (min_value < 0) :
			raise ParameterSetException("Valores negativos não são suportados para min_value")

		if (max_value <= min_value) :
			raise ParameterSetException("O valor mínimo não deve exceder ou ser igual ao valor máximo")

		if (qt_numbers < 1) :
			raise ParameterSetException("A quantidade de números a serem sorteados deve ser maior que 0")

		#atributos da classe
		self.min_value = min_value
		self.max_value = max_value
		self.qt_numbers = qt_numbers

		self.tickets = []
		self.sorted_numbers = []
		self.winner_tickets = self._build_empty_winner_tickets()

	# funções auxiliares
	def _build_empty_winner_tickets(self) :
		return [[] for _ in range(self.qt_numbers + 1)]

	def _range_of_available_numbers(self) :
		return self.max_value - self.min_value + 1

	def _check_qt_numbers_fits_range(self) :
		if self.qt_numbers > self._range_of_available_numbers() :
			raise ParameterSetException(f"QT_NUMBERS | {self.qt_numbers} deve ser menor que a quantidade de números disponíveis no intervalo entre {self.min_value} ~ {self.max_value}")

	# funções para setar parâmetros da instância
	def set_min_value (self, new_value) :
		if (new_value < 0) :
			raise ParameterSetException("Valores negativos não são suportados")
		
		if (new_value >= self.max_value) :
			raise ParameterSetException("O valor minímo não deve exceder o valor máximo")

		old_value = self.min_value
		self.min_value = new_value
	
		try:
			self._check_qt_numbers_fits_range()
		except ParameterSetException :
			self.min_value = old_value
			raise

		return f"MIN_VALUE atualizado: {self.min_value}"

	def set_max_value(self, new_value) :
		if(new_value <= self.min_value) :
			raise ParameterSetException("O valor máximo não pode ser igual ou menor que o minímo")

		old_value = self.max_value
		self.max_value = new_value

		try :
			self._check_qt_numbers_fits_range()
		except ParameterSetException:
			self.max_value = old_value
			raise

		return f"MAX_VALUE atualizado: {self.max_value}"

	def qtd_numeros_sorteados(self, qtd):
		if (qtd < 1) :
			raise ParameterSetException("A quantidade de números a serem sorteados deve ser maior que 0")

		if (qtd > self._range_of_available_numbers()) :
			raise ParameterSetException("A quantidade de números a serem sorteados deve ser menor que a quantidade de números disponíveis para sorteio")

		self.qt_numbers = qtd
		self.winner_tickets = self._build_empty_winner_tickets()

		return f"QT_NUMBERS atualizado: {self.qt_numbers}"

	# funções para realizar o sorteio
	def add_ticket(self, numbers_input) :
		if (not numbers_input or not str(numbers_input).strip()) :
			raise AddTicketException("A aposta não deve estar vazia")

		# dou parse na string pra separar os números em elementos de um array
		try :
			parsed_numbers = [int(n) for n in numbers_input.split()]
		except ValueError :
			raise AddTicketException("A aposta deve conter somente valores numéricos")

		# removo números repetidos do array dos números da aposta
		qt_nums_informados = len(parsed_numbers)
		parsed_numbers = set(parsed_numbers)

		# verifico se houve uma mudança na quantidade de elementos (se teve, quer dizer que tinham valores repetidos)
		if (qt_nums_informados != len(parsed_numbers)) :
			raise AddTicketException(f"A aposta contém números repetidos (a aposta deve conter {self.qt_numbers} números únicos)")

		# se não tinha repetidos, vejo se tem a quantidade de números préviamente (ou não) configuradas
		if (qt_nums_informados != self.qt_numbers) :
			raise AddTicketException(f"A aposta deve conter {self.qt_numbers} números")

		# crio um conjunto dos números que podem ser atribuídos à uma aposta
		availabe_numbers_set = set(range(self.min_value, self.max_value + 1))

		# e vejo se os números inseridos pertencem ao conjunto (de modo que o conjuntos dos valores apostados deve ser um subconjunto dos números válidos)
		if (not parsed_numbers.issubset(availabe_numbers_set)) :
			raise AddTicketException(f"A aposta deve conter somente valores no intervalo de {self.min_value} a {self.max_value}")

		self.tickets.append(parsed_numbers)

		return f"A aposta {parsed_numbers} foi adicionada com sucesso"

	def reset_tickets(self) :
		self.tickets.clear()

	def fetch_tickets(self) :
		return self.tickets.copy()

	def realizar_sorteio(self) :
		self.winner_tickets = self._build_empty_winner_tickets()
		self.sorted_numbers = random.sample(range(self.min_value, self.max_value + 1), self.qt_numbers)
		sorted_set = set(self.sorted_numbers)

		for ticket in self.tickets :
			qt_matches = len(sorted_set & ticket)

			if (qt_matches != 0) :
				self.winner_tickets[qt_matches].append(ticket)

		return self.sorted_numbers, self.winner_tickets