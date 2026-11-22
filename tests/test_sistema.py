import threading
import unittest
from datetime import date
from decimal import Decimal

from sistema.biblioteca import Biblioteca
from sistema.comparacao import total_multas_funcional, total_multas_imperativo
from sistema.excecoes import (
    DevolucaoInvalidaError,
    LivroIndisponivelError,
    RegistroNaoEncontradoError,
)
from sistema.funcoes_puras import (
    calcular_multa,
    contar_emprestimos_por_usuario,
    contar_livros_por_categoria,
    filtrar_livros_por_categoria,
    gerar_relatorio_multas,
)

REFERENCIA = date(2026, 11, 22)


def montar_biblioteca() -> Biblioteca:
    biblioteca = Biblioteca()
    biblioteca.cadastrar_livro("Dom Casmurro", "Machado", "Romance")
    biblioteca.cadastrar_livro("Algoritmos", "Cormen", "Computação")
    biblioteca.cadastrar_livro("Código Limpo", "Martin", "Computação")
    biblioteca.cadastrar_usuario("Ana", "1")
    biblioteca.cadastrar_usuario("Bruno", "2")
    return biblioteca


class TesteFuncoesPuras(unittest.TestCase):
    def test_multa_dois_reais_por_dia(self):
        self.assertEqual(calcular_multa(5), Decimal("10.00"))

    def test_multa_sem_atraso_e_zero(self):
        self.assertEqual(calcular_multa(0), Decimal("0.00"))
        self.assertEqual(calcular_multa(-3), Decimal("0.00"))

    def test_multa_e_deterministica(self):
        self.assertEqual(calcular_multa(7), calcular_multa(7))

    def test_filtro_por_categoria_nao_altera_colecao(self):
        biblioteca = montar_biblioteca()
        livros = biblioteca.listar_livros()
        copia = tuple(livros)
        filtrados = filtrar_livros_por_categoria(livros, "computação")
        self.assertEqual(len(filtrados), 2)
        self.assertEqual(livros, copia)

    def test_livros_por_categoria(self):
        biblioteca = montar_biblioteca()
        self.assertEqual(
            dict(contar_livros_por_categoria(biblioteca.listar_livros())),
            {"Romance": 1, "Computação": 2},
        )


class TesteBiblioteca(unittest.TestCase):
    def test_livro_nao_pode_ser_emprestado_duas_vezes(self):
        biblioteca = montar_biblioteca()
        biblioteca.registrar_emprestimo(1, 1, REFERENCIA)
        with self.assertRaises(LivroIndisponivelError):
            biblioteca.registrar_emprestimo(1, 2, REFERENCIA)

    def test_devolucao_libera_livro(self):
        biblioteca = montar_biblioteca()
        emprestimo = biblioteca.registrar_emprestimo(1, 1, date(2026, 11, 1))
        biblioteca.registrar_devolucao(emprestimo.identificador, date(2026, 11, 5))
        self.assertTrue(biblioteca.livro_esta_disponivel(1))
        self.assertEqual(
            biblioteca.consultar_emprestimo(emprestimo.identificador).data_devolucao, date(2026, 11, 5)
        )

    def test_devolucao_dupla_e_rejeitada(self):
        biblioteca = montar_biblioteca()
        emprestimo = biblioteca.registrar_emprestimo(1, 1, date(2026, 11, 1))
        biblioteca.registrar_devolucao(emprestimo.identificador, date(2026, 11, 5))
        with self.assertRaises(DevolucaoInvalidaError):
            biblioteca.registrar_devolucao(emprestimo.identificador, date(2026, 11, 6))

    def test_registro_inexistente(self):
        biblioteca = montar_biblioteca()
        with self.assertRaises(RegistroNaoEncontradoError):
            biblioteca.registrar_emprestimo(99, 1, REFERENCIA)

    def test_atraso_apenas_apos_data_prevista(self):
        biblioteca = montar_biblioteca()
        emprestimo = biblioteca.registrar_emprestimo(1, 1, date(2026, 11, 8))
        self.assertFalse(emprestimo.esta_atrasado(date(2026, 11, 22)))
        self.assertTrue(emprestimo.esta_atrasado(date(2026, 11, 23)))
        self.assertEqual(emprestimo.dias_de_atraso(date(2026, 11, 25)), 3)

    def test_emprestimo_devolvido_nao_gera_multa(self):
        biblioteca = montar_biblioteca()
        emprestimo = biblioteca.registrar_emprestimo(1, 1, date(2026, 9, 1))
        biblioteca.registrar_devolucao(emprestimo.identificador, date(2026, 11, 20))
        relatorio = biblioteca.gerar_relatorio_multas(REFERENCIA)
        self.assertEqual(relatorio.itens, ())
        self.assertEqual(relatorio.total, Decimal("0.00"))

    def test_relatorio_de_multas(self):
        biblioteca = montar_biblioteca()
        biblioteca.registrar_emprestimo(1, 1, date(2026, 10, 1))
        biblioteca.registrar_emprestimo(2, 2, date(2026, 10, 20))
        biblioteca.registrar_emprestimo(3, 2, date(2026, 11, 20))
        antes = biblioteca.listar_emprestimos()
        relatorio = gerar_relatorio_multas(antes, REFERENCIA)
        self.assertEqual(len(relatorio.itens), 2)
        self.assertEqual(relatorio.total, Decimal("114.00"))
        self.assertEqual(antes, biblioteca.listar_emprestimos())

    def test_estatisticas(self):
        biblioteca = montar_biblioteca()
        biblioteca.registrar_emprestimo(1, 1, date(2026, 10, 1))
        devolvido = biblioteca.registrar_emprestimo(2, 1, date(2026, 10, 1))
        biblioteca.registrar_devolucao(devolvido.identificador, date(2026, 10, 3))
        estatisticas = biblioteca.gerar_estatisticas(REFERENCIA)
        self.assertEqual(estatisticas.emprestimos_ativos, 1)
        self.assertEqual(estatisticas.emprestimos_ativos_em_atraso, 1)
        self.assertEqual(estatisticas.valor_total_multas, Decimal("76.00"))
        self.assertEqual(dict(estatisticas.emprestimos_por_usuario), {"Ana (1)": 2})
        self.assertEqual(
            dict(contar_emprestimos_por_usuario(biblioteca.listar_emprestimos())), {"Ana (1)": 2}
        )

    def test_comparacao_imperativo_funcional(self):
        biblioteca = montar_biblioteca()
        biblioteca.registrar_emprestimo(1, 1, date(2026, 10, 1))
        biblioteca.registrar_emprestimo(2, 2, date(2026, 10, 20))
        emprestimos = biblioteca.listar_emprestimos()
        self.assertEqual(
            total_multas_imperativo(emprestimos, REFERENCIA),
            total_multas_funcional(emprestimos, REFERENCIA),
        )

    def test_concorrencia_um_unico_vencedor(self):
        biblioteca = montar_biblioteca()
        barreira = threading.Barrier(2)
        sucessos = []

        def tentar(identificador_usuario):
            barreira.wait()
            try:
                biblioteca.registrar_emprestimo(1, identificador_usuario, REFERENCIA)
                sucessos.append(identificador_usuario)
            except LivroIndisponivelError:
                pass

        threads = [threading.Thread(target=tentar, args=(i,)) for i in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(sucessos), 1)
        self.assertEqual(len(biblioteca.consultar_emprestimos_ativos()), 1)


if __name__ == "__main__":
    unittest.main()
