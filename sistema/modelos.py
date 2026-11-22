from datetime import date
from typing import Optional

from sistema.excecoes import DadosInvalidosError, DevolucaoInvalidaError


class Livro:
    def __init__(self, identificador: int, titulo: str, autor: str, categoria: str):
        self._identificador = identificador
        self._titulo = titulo
        self._autor = autor
        self._categoria = categoria

    @property
    def identificador(self) -> int:
        return self._identificador

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def autor(self) -> str:
        return self._autor

    @property
    def categoria(self) -> str:
        return self._categoria

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Livro) and self._identificador == outro._identificador

    def __hash__(self) -> int:
        return hash(("Livro", self._identificador))

    def __repr__(self) -> str:
        return f"Livro({self._identificador}, {self._titulo!r}, {self._autor!r}, {self._categoria!r})"


class Usuario:
    def __init__(self, identificador: int, nome: str, matricula: str):
        self._identificador = identificador
        self._nome = nome
        self._matricula = matricula

    @property
    def identificador(self) -> int:
        return self._identificador

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def matricula(self) -> str:
        return self._matricula

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Usuario) and self._identificador == outro._identificador

    def __hash__(self) -> int:
        return hash(("Usuario", self._identificador))

    def __repr__(self) -> str:
        return f"Usuario({self._identificador}, {self._nome!r}, {self._matricula!r})"


class Emprestimo:
    def __init__(
        self,
        identificador: int,
        livro: Livro,
        usuario: Usuario,
        data_emprestimo: date,
        data_prevista_devolucao: date,
        data_devolucao: Optional[date] = None,
    ):
        if data_prevista_devolucao < data_emprestimo:
            raise DadosInvalidosError("A data prevista não pode ser anterior à data do empréstimo.")
        if data_devolucao is not None and data_devolucao < data_emprestimo:
            raise DadosInvalidosError("A devolução não pode ser anterior à data do empréstimo.")
        self._identificador = identificador
        self._livro = livro
        self._usuario = usuario
        self._data_emprestimo = data_emprestimo
        self._data_prevista_devolucao = data_prevista_devolucao
        self._data_devolucao = data_devolucao

    @property
    def identificador(self) -> int:
        return self._identificador

    @property
    def livro(self) -> Livro:
        return self._livro

    @property
    def usuario(self) -> Usuario:
        return self._usuario

    @property
    def data_emprestimo(self) -> date:
        return self._data_emprestimo

    @property
    def data_prevista_devolucao(self) -> date:
        return self._data_prevista_devolucao

    @property
    def data_devolucao(self) -> Optional[date]:
        return self._data_devolucao

    @property
    def ativo(self) -> bool:
        return self._data_devolucao is None

    def esta_atrasado(self, data_referencia: date) -> bool:
        return self.ativo and data_referencia > self._data_prevista_devolucao

    def dias_de_atraso(self, data_referencia: date) -> int:
        if not self.esta_atrasado(data_referencia):
            return 0
        return (data_referencia - self._data_prevista_devolucao).days

    def com_devolucao(self, data_devolucao: date) -> "Emprestimo":
        if not self.ativo:
            raise DevolucaoInvalidaError(f"O empréstimo {self._identificador} já foi devolvido.")
        return Emprestimo(
            self._identificador,
            self._livro,
            self._usuario,
            self._data_emprestimo,
            self._data_prevista_devolucao,
            data_devolucao,
        )

    def __repr__(self) -> str:
        return (
            f"Emprestimo({self._identificador}, livro={self._livro.identificador}, "
            f"usuario={self._usuario.identificador}, emprestimo={self._data_emprestimo}, "
            f"prevista={self._data_prevista_devolucao}, devolucao={self._data_devolucao})"
        )
