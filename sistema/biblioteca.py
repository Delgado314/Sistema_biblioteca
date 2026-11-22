import threading
from datetime import date, timedelta
from typing import Dict, Tuple

from sistema import funcoes_puras
from sistema.excecoes import (
    DadosInvalidosError,
    LivroIndisponivelError,
    RegistroNaoEncontradoError,
)
from sistema.funcoes_puras import Estatisticas, RelatorioMultas
from sistema.modelos import Emprestimo, Livro, Usuario

PRAZO_PADRAO_DIAS = 14


class Biblioteca:
    def __init__(self):
        self._livros: Dict[int, Livro] = {}
        self._usuarios: Dict[int, Usuario] = {}
        self._emprestimos: Dict[int, Emprestimo] = {}
        self._proximo_livro = 1
        self._proximo_usuario = 1
        self._proximo_emprestimo = 1
        self._trava = threading.RLock()

    def cadastrar_livro(self, titulo: str, autor: str, categoria: str) -> Livro:
        if not (titulo.strip() and autor.strip() and categoria.strip()):
            raise DadosInvalidosError("Título, autor e categoria são obrigatórios.")
        with self._trava:
            livro = Livro(self._proximo_livro, titulo.strip(), autor.strip(), categoria.strip())
            self._livros[livro.identificador] = livro
            self._proximo_livro += 1
            return livro

    def cadastrar_usuario(self, nome: str, matricula: str) -> Usuario:
        if not (nome.strip() and matricula.strip()):
            raise DadosInvalidosError("Nome e matrícula são obrigatórios.")
        with self._trava:
            if any(usuario.matricula == matricula.strip() for usuario in self._usuarios.values()):
                raise DadosInvalidosError(f"A matrícula {matricula} já está cadastrada.")
            usuario = Usuario(self._proximo_usuario, nome.strip(), matricula.strip())
            self._usuarios[usuario.identificador] = usuario
            self._proximo_usuario += 1
            return usuario

    def consultar_livro(self, identificador: int) -> Livro:
        with self._trava:
            return self._obter(self._livros, identificador, "Livro")

    def consultar_usuario(self, identificador: int) -> Usuario:
        with self._trava:
            return self._obter(self._usuarios, identificador, "Usuário")

    def consultar_emprestimo(self, identificador: int) -> Emprestimo:
        with self._trava:
            return self._obter(self._emprestimos, identificador, "Empréstimo")

    def listar_livros(self) -> Tuple[Livro, ...]:
        with self._trava:
            return tuple(self._livros.values())

    def listar_usuarios(self) -> Tuple[Usuario, ...]:
        with self._trava:
            return tuple(self._usuarios.values())

    def listar_emprestimos(self) -> Tuple[Emprestimo, ...]:
        with self._trava:
            return tuple(self._emprestimos.values())

    def consultar_livros_por_categoria(self, categoria: str) -> Tuple[Livro, ...]:
        return funcoes_puras.filtrar_livros_por_categoria(self.listar_livros(), categoria)

    def consultar_emprestimos_do_usuario(self, identificador_usuario: int) -> Tuple[Emprestimo, ...]:
        usuario = self.consultar_usuario(identificador_usuario)
        return tuple(filter(lambda emprestimo: emprestimo.usuario == usuario, self.listar_emprestimos()))

    def consultar_emprestimos_ativos(self) -> Tuple[Emprestimo, ...]:
        return funcoes_puras.filtrar_emprestimos_ativos(self.listar_emprestimos())

    def consultar_emprestimos_atrasados(self, data_referencia: date) -> Tuple[Emprestimo, ...]:
        return funcoes_puras.filtrar_emprestimos_atrasados(self.listar_emprestimos(), data_referencia)

    def livro_esta_disponivel(self, identificador_livro: int) -> bool:
        with self._trava:
            self._obter(self._livros, identificador_livro, "Livro")
            return not self._livro_esta_emprestado(identificador_livro)

    def registrar_emprestimo(
        self,
        identificador_livro: int,
        identificador_usuario: int,
        data_emprestimo: date,
        prazo_dias: int = PRAZO_PADRAO_DIAS,
    ) -> Emprestimo:
        if prazo_dias <= 0:
            raise DadosInvalidosError("O prazo de empréstimo deve ser maior que zero.")
        with self._trava:
            livro = self._obter(self._livros, identificador_livro, "Livro")
            usuario = self._obter(self._usuarios, identificador_usuario, "Usuário")
            if self._livro_esta_emprestado(livro.identificador):
                raise LivroIndisponivelError(f"O livro '{livro.titulo}' já está emprestado.")
            emprestimo = Emprestimo(
                self._proximo_emprestimo,
                livro,
                usuario,
                data_emprestimo,
                data_emprestimo + timedelta(days=prazo_dias),
            )
            self._emprestimos[emprestimo.identificador] = emprestimo
            self._proximo_emprestimo += 1
            return emprestimo

    def registrar_devolucao(self, identificador_emprestimo: int, data_devolucao: date) -> Emprestimo:
        with self._trava:
            atual = self._obter(self._emprestimos, identificador_emprestimo, "Empréstimo")
            atualizado = atual.com_devolucao(data_devolucao)
            self._emprestimos[identificador_emprestimo] = atualizado
            return atualizado

    def gerar_relatorio_multas(self, data_referencia: date) -> RelatorioMultas:
        return funcoes_puras.gerar_relatorio_multas(self.listar_emprestimos(), data_referencia)

    def gerar_estatisticas(self, data_referencia: date) -> Estatisticas:
        with self._trava:
            livros = self.listar_livros()
            emprestimos = self.listar_emprestimos()
        return funcoes_puras.gerar_estatisticas(livros, emprestimos, data_referencia)

    def _livro_esta_emprestado(self, identificador_livro: int) -> bool:
        return any(
            emprestimo.ativo and emprestimo.livro.identificador == identificador_livro
            for emprestimo in self._emprestimos.values()
        )

    @staticmethod
    def _obter(registros: dict, identificador: int, rotulo: str):
        if identificador not in registros:
            raise RegistroNaoEncontradoError(f"{rotulo} {identificador} não encontrado.")
        return registros[identificador]
