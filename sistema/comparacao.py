from datetime import date
from decimal import Decimal
from functools import reduce
from typing import Iterable

from sistema.funcoes_puras import VALOR_MULTA_DIARIA, ZERO, calcular_multa
from sistema.modelos import Emprestimo


def total_multas_imperativo(
    emprestimos: Iterable[Emprestimo],
    data_referencia: date,
    valor_diario: Decimal = VALOR_MULTA_DIARIA,
) -> Decimal:
    total = Decimal("0.00")
    for emprestimo in emprestimos:
        if emprestimo.ativo and data_referencia > emprestimo.data_prevista_devolucao:
            dias = (data_referencia - emprestimo.data_prevista_devolucao).days
            total += calcular_multa(dias, valor_diario)
    return total


def total_multas_funcional(
    emprestimos: Iterable[Emprestimo],
    data_referencia: date,
    valor_diario: Decimal = VALOR_MULTA_DIARIA,
) -> Decimal:
    atrasados = filter(lambda emprestimo: emprestimo.esta_atrasado(data_referencia), emprestimos)
    dias = map(lambda emprestimo: emprestimo.dias_de_atraso(data_referencia), atrasados)
    multas = map(lambda quantidade: calcular_multa(quantidade, valor_diario), dias)
    return reduce(lambda acumulado, multa: acumulado + multa, multas, ZERO)
