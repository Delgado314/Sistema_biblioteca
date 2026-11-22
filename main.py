import threading
from datetime import date

from sistema.biblioteca import Biblioteca
from sistema.comparacao import total_multas_funcional, total_multas_imperativo
from sistema.excecoes import LivroIndisponivelError
from sistema.funcoes_puras import (
    calcular_multa,
    formatar_estatisticas,
    formatar_moeda,
    formatar_relatorio_multas,
)

DATA_REFERENCIA = date(2026, 11, 22)


def titulo(texto: str) -> None:
    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)


def popular_biblioteca() -> Biblioteca:
    biblioteca = Biblioteca()
    biblioteca.cadastrar_livro("Dom Casmurro", "Machado de Assis", "Romance")
    biblioteca.cadastrar_livro("O Alienista", "Machado de Assis", "Romance")
    biblioteca.cadastrar_livro("Algoritmos", "Thomas Cormen", "Computação")
    biblioteca.cadastrar_livro("Código Limpo", "Robert Martin", "Computação")
    biblioteca.cadastrar_livro("Sapiens", "Yuval Harari", "História")
    biblioteca.cadastrar_livro("1984", "George Orwell", "Ficção")
    biblioteca.cadastrar_usuario("Ana Souza", "2024001")
    biblioteca.cadastrar_usuario("Bruno Lima", "2024002")
    biblioteca.cadastrar_usuario("Carla Dias", "2024003")
    biblioteca.registrar_emprestimo(1, 1, date(2026, 10, 1))
    biblioteca.registrar_emprestimo(3, 1, date(2026, 11, 10))
    biblioteca.registrar_emprestimo(4, 2, date(2026, 10, 20))
    biblioteca.registrar_emprestimo(5, 3, date(2026, 9, 1))
    biblioteca.registrar_devolucao(4, date(2026, 9, 10))
    biblioteca.registrar_emprestimo(5, 3, date(2026, 11, 1))
    return biblioteca


def demonstrar_cadastros(biblioteca: Biblioteca) -> None:
    titulo("1. Livros, usuários e empréstimos cadastrados")
    for livro in biblioteca.listar_livros():
        situacao = "disponível" if biblioteca.livro_esta_disponivel(livro.identificador) else "emprestado"
        print(f"  {livro} - {situacao}")
    for usuario in biblioteca.listar_usuarios():
        print(f"  {usuario}")
    for emprestimo in biblioteca.listar_emprestimos():
        print(f"  {emprestimo}")


def demonstrar_filtragem(biblioteca: Biblioteca) -> None:
    titulo("2. Filtragem de livros por categoria (filter)")
    colecao_original = biblioteca.listar_livros()
    filtrados = biblioteca.consultar_livros_por_categoria("Computação")
    for livro in filtrados:
        print(f"  {livro}")
    print(f"  Coleção original preservada: {colecao_original == biblioteca.listar_livros()}")
    print(f"  Total original: {len(colecao_original)} | Total filtrado: {len(filtrados)}")


def demonstrar_multa_pura() -> None:
    titulo("3. Função pura de cálculo de multa")
    for dias in (0, 1, 7, 19, 38):
        print(f"  {dias} dia(s) de atraso -> {formatar_moeda(calcular_multa(dias))}")


def demonstrar_atrasados(biblioteca: Biblioteca) -> None:
    titulo("4. Empréstimos ativos em atraso (filter)")
    for emprestimo in biblioteca.consultar_emprestimos_atrasados(DATA_REFERENCIA):
        print(f"  {emprestimo} - {emprestimo.dias_de_atraso(DATA_REFERENCIA)} dia(s)")


def demonstrar_relatorio(biblioteca: Biblioteca) -> None:
    titulo("5. Relatório de multas (filter + map + reduce)")
    emprestimos_antes = biblioteca.listar_emprestimos()
    relatorio = biblioteca.gerar_relatorio_multas(DATA_REFERENCIA)
    print(formatar_relatorio_multas(relatorio))
    print(f"  Dados originais preservados: {emprestimos_antes == biblioteca.listar_emprestimos()}")


def demonstrar_estatisticas(biblioteca: Biblioteca) -> None:
    titulo("6. Estatísticas")
    print(formatar_estatisticas(biblioteca.gerar_estatisticas(DATA_REFERENCIA)))


def demonstrar_comparacao(biblioteca: Biblioteca) -> None:
    titulo("7. Comparação: imperativo x funcional (total de multas)")
    emprestimos = biblioteca.listar_emprestimos()
    imperativo = total_multas_imperativo(emprestimos, DATA_REFERENCIA)
    funcional = total_multas_funcional(emprestimos, DATA_REFERENCIA)
    print(f"  Imperativo: {formatar_moeda(imperativo)}")
    print(f"  Funcional : {formatar_moeda(funcional)}")
    print(f"  Resultados equivalentes: {imperativo == funcional}")


def demonstrar_regras_de_negocio(biblioteca: Biblioteca) -> None:
    titulo("8. Regras de negócio: livro já emprestado e devolução")
    try:
        biblioteca.registrar_emprestimo(1, 2, DATA_REFERENCIA)
    except LivroIndisponivelError as erro:
        print(f"  Bloqueado: {erro}")
    devolvido = biblioteca.registrar_devolucao(1, DATA_REFERENCIA)
    print(f"  Devolvido: {devolvido}")
    print(f"  Livro 1 disponível: {biblioteca.livro_esta_disponivel(1)}")
    novo = biblioteca.registrar_emprestimo(1, 2, DATA_REFERENCIA)
    print(f"  Novo empréstimo: {novo}")
    relatorio = biblioteca.gerar_relatorio_multas(DATA_REFERENCIA)
    print(formatar_relatorio_multas(relatorio))


def demonstrar_concorrencia(biblioteca: Biblioteca) -> None:
    titulo("9. Concorrência: três usuários tentam o mesmo livro ao mesmo tempo")
    identificadores = tuple(usuario.identificador for usuario in biblioteca.listar_usuarios())
    barreira = threading.Barrier(len(identificadores))
    resultados = []
    trava_resultados = threading.Lock()

    def tentar(identificador_usuario: int) -> None:
        barreira.wait()
        try:
            biblioteca.registrar_emprestimo(6, identificador_usuario, DATA_REFERENCIA)
            resultado = (identificador_usuario, "conseguiu")
        except LivroIndisponivelError:
            resultado = (identificador_usuario, "bloqueado")
        with trava_resultados:
            resultados.append(resultado)

    threads = [threading.Thread(target=tentar, args=(identificador,)) for identificador in identificadores]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for identificador, resultado in sorted(resultados):
        print(f"  Usuário {identificador}: {resultado}")
    vencedores = len([r for r in resultados if r[1] == "conseguiu"])
    print(f"  Empréstimos ativos do livro 6: {vencedores}")


def main() -> None:
    biblioteca = popular_biblioteca()
    demonstrar_cadastros(biblioteca)
    demonstrar_filtragem(biblioteca)
    demonstrar_multa_pura()
    demonstrar_atrasados(biblioteca)
    demonstrar_relatorio(biblioteca)
    demonstrar_estatisticas(biblioteca)
    demonstrar_comparacao(biblioteca)
    demonstrar_regras_de_negocio(biblioteca)
    demonstrar_concorrencia(biblioteca)


if __name__ == "__main__":
    main()
