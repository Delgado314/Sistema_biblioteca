from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import reduce
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from sistema.modelos import Emprestimo, Livro

VALOR_MULTA_DIARIA = Decimal("2.00")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ItemMulta:
    identificador_emprestimo: int
    titulo_livro: str
    nome_usuario: str
    dias_atraso: int
    valor_multa: Decimal


@dataclass(frozen=True)
class RelatorioMultas:
    data_referencia: date
    itens: Tuple[ItemMulta, ...]
    total: Decimal


@dataclass(frozen=True)
class Estatisticas:
    livros_por_categoria: Mapping[str, int]
    emprestimos_por_usuario: Mapping[str, int]
    emprestimos_ativos: int
    emprestimos_ativos_em_atraso: int
    valor_total_multas: Decimal


def filtrar_livros_por_categoria(livros: Iterable[Livro], categoria: str) -> Tuple[Livro, ...]:
    return tuple(filter(lambda livro: livro.categoria.casefold() == categoria.casefold(), livros))


def calcular_multa(dias_atraso: int, valor_diario: Decimal = VALOR_MULTA_DIARIA) -> Decimal:
    return Decimal(max(dias_atraso, 0)) * valor_diario


def filtrar_emprestimos_ativos(emprestimos: Iterable[Emprestimo]) -> Tuple[Emprestimo, ...]:
    return tuple(filter(lambda emprestimo: emprestimo.ativo, emprestimos))


def filtrar_emprestimos_atrasados(
    emprestimos: Iterable[Emprestimo], data_referencia: date
) -> Tuple[Emprestimo, ...]:
    return tuple(filter(lambda emprestimo: emprestimo.esta_atrasado(data_referencia), emprestimos))


def criar_item_multa(
    emprestimo: Emprestimo, data_referencia: date, valor_diario: Decimal = VALOR_MULTA_DIARIA
) -> ItemMulta:
    dias = emprestimo.dias_de_atraso(data_referencia)
    return ItemMulta(
        identificador_emprestimo=emprestimo.identificador,
        titulo_livro=emprestimo.livro.titulo,
        nome_usuario=emprestimo.usuario.nome,
        dias_atraso=dias,
        valor_multa=calcular_multa(dias, valor_diario),
    )


def somar_valores(valores: Iterable[Decimal]) -> Decimal:
    return reduce(lambda acumulado, valor: acumulado + valor, valores, ZERO)


def gerar_relatorio_multas(
    emprestimos: Iterable[Emprestimo],
    data_referencia: date,
    valor_diario: Decimal = VALOR_MULTA_DIARIA,
) -> RelatorioMultas:
    atrasados = filter(lambda emprestimo: emprestimo.esta_atrasado(data_referencia), emprestimos)
    itens = tuple(map(lambda emprestimo: criar_item_multa(emprestimo, data_referencia, valor_diario), atrasados))
    total = reduce(lambda acumulado, item: acumulado + item.valor_multa, itens, ZERO)
    return RelatorioMultas(data_referencia=data_referencia, itens=itens, total=total)


def contar_livros_por_categoria(livros: Iterable[Livro]) -> Mapping[str, int]:
    contagem = reduce(
        lambda acumulado, livro: {**acumulado, livro.categoria: acumulado.get(livro.categoria, 0) + 1},
        livros,
        {},
    )
    return MappingProxyType(contagem)


def rotulo_usuario(emprestimo: Emprestimo) -> str:
    return f"{emprestimo.usuario.nome} ({emprestimo.usuario.matricula})"


def contar_emprestimos_por_usuario(emprestimos: Iterable[Emprestimo]) -> Mapping[str, int]:
    contagem = reduce(
        lambda acumulado, emprestimo: {
            **acumulado,
            rotulo_usuario(emprestimo): acumulado.get(rotulo_usuario(emprestimo), 0) + 1,
        },
        emprestimos,
        {},
    )
    return MappingProxyType(contagem)


def contar_emprestimos_ativos(emprestimos: Iterable[Emprestimo]) -> int:
    return len(filtrar_emprestimos_ativos(emprestimos))


def contar_emprestimos_atrasados(emprestimos: Iterable[Emprestimo], data_referencia: date) -> int:
    return len(filtrar_emprestimos_atrasados(emprestimos, data_referencia))


def calcular_valor_total_multas(
    emprestimos: Iterable[Emprestimo],
    data_referencia: date,
    valor_diario: Decimal = VALOR_MULTA_DIARIA,
) -> Decimal:
    atrasados = filtrar_emprestimos_atrasados(emprestimos, data_referencia)
    multas = map(lambda emprestimo: calcular_multa(emprestimo.dias_de_atraso(data_referencia), valor_diario), atrasados)
    return somar_valores(multas)


def gerar_estatisticas(
    livros: Iterable[Livro], emprestimos: Iterable[Emprestimo], data_referencia: date
) -> Estatisticas:
    livros_tupla = tuple(livros)
    emprestimos_tupla = tuple(emprestimos)
    return Estatisticas(
        livros_por_categoria=contar_livros_por_categoria(livros_tupla),
        emprestimos_por_usuario=contar_emprestimos_por_usuario(emprestimos_tupla),
        emprestimos_ativos=contar_emprestimos_ativos(emprestimos_tupla),
        emprestimos_ativos_em_atraso=contar_emprestimos_atrasados(emprestimos_tupla, data_referencia),
        valor_total_multas=calcular_valor_total_multas(emprestimos_tupla, data_referencia),
    )


def formatar_moeda(valor: Decimal) -> str:
    return f"R$ {valor:.2f}".replace(".", ",")


def formatar_data(data: date) -> str:
    return data.strftime("%d/%m/%Y")


def formatar_item_multa(item: ItemMulta) -> str:
    return (
        f"  Empréstimo {item.identificador_emprestimo}: '{item.titulo_livro}' - {item.nome_usuario} - "
        f"{item.dias_atraso} dia(s) de atraso - {formatar_moeda(item.valor_multa)}"
    )


def formatar_relatorio_multas(relatorio: RelatorioMultas) -> str:
    cabecalho = (f"Relatório de multas (referência: {formatar_data(relatorio.data_referencia)})",)
    linhas = tuple(map(formatar_item_multa, relatorio.itens)) or ("  Nenhum empréstimo ativo em atraso.",)
    rodape = (f"  Total de multas: {formatar_moeda(relatorio.total)}",)
    return "\n".join(cabecalho + linhas + rodape)


def formatar_contagem(titulo: str, contagem: Mapping[str, int]) -> str:
    linhas = tuple(map(lambda par: f"  {par[0]}: {par[1]}", sorted(contagem.items())))
    return "\n".join((titulo,) + linhas)


def formatar_estatisticas(estatisticas: Estatisticas) -> str:
    return "\n".join(
        (
            formatar_contagem("Livros por categoria:", estatisticas.livros_por_categoria),
            formatar_contagem("Empréstimos por usuário:", estatisticas.emprestimos_por_usuario),
            f"Empréstimos ativos: {estatisticas.emprestimos_ativos}",
            f"Empréstimos ativos em atraso: {estatisticas.emprestimos_ativos_em_atraso}",
            f"Valor total das multas: {formatar_moeda(estatisticas.valor_total_multas)}",
        )
    )
