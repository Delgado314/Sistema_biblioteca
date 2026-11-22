# Sistema de Gerenciamento de Biblioteca

Atividade Prática — Linguagens de Programação (Orientação a Objetos e Programação Funcional).

## Integrantes

- José Lucas 
- Alvaro Antônio

## Linguagem

Python 3.10 ou superior. Apenas a biblioteca padrão é usada, sem dependências externas.

## Como executar

```bash
python3 main.py
```

Executa uma demonstração com todas as funcionalidades.

```bash
python3 -m unittest discover -v
```

Executa os testes automatizados (15 testes).

## Estrutura

```
main.py                    demonstração executável
sistema/
  modelos.py               Livro, Usuario, Emprestimo
  biblioteca.py            Biblioteca (operações com efeitos colaterais)
  funcoes_puras.py         funções puras, relatório e estatísticas
  comparacao.py            versão imperativa x funcional
  excecoes.py              exceções de domínio
tests/test_sistema.py      testes
```

## Funcionalidades

- Cadastro e consulta de livros e usuários.
- Registro de empréstimos (prazo padrão de 14 dias) e devoluções.
- Consulta de empréstimos: todos, ativos, atrasados e por usuário.
- Filtragem de livros por categoria.
- Cálculo de multa de R$ 2,00 por dia de atraso.
- Relatório de multas dos empréstimos ativos e atrasados, com data de referência informada.
- Estatísticas: livros por categoria, empréstimos por usuário, empréstimos ativos, empréstimos ativos em atraso e valor total das multas.
- Comparação entre implementação imperativa e funcional do total de multas.

## Modelagem orientada a objetos

| Classe | Responsabilidade |
|---|---|
| `Livro` | Dados de um exemplar do acervo (id, título, autor, categoria). |
| `Usuario` | Dados de um usuário (id, nome, matrícula). |
| `Emprestimo` | Associa um `Livro` a um `Usuario`, com datas. Sabe se está ativo, atrasado e quantos dias de atraso tem. |
| `Biblioteca` | Guarda o estado, aplica as regras de negócio e delega os cálculos às funções puras. |

Encapsulamento: atributos privados (`_atributo`) expostos apenas por propriedades somente leitura. O estado da `Biblioteca` (dicionários internos) nunca é entregue diretamente; as consultas devolvem tuplas novas.

Relacionamentos: um `Usuario` possui vários `Emprestimo` (0..*); cada `Emprestimo` referencia exatamente um `Usuario` e um `Livro`; a `Biblioteca` agrega `Livro`, `Usuario` e `Emprestimo`.

## Programação funcional

| Requisito | Onde |
|---|---|
| Filtragem de livros (`filter`) | `filtrar_livros_por_categoria` |
| Cálculo de multa (função pura) | `calcular_multa` |
| Empréstimos atrasados (`filter`) | `filtrar_emprestimos_atrasados` |
| Relatório de multas (`filter` + `map` + `reduce`) | `gerar_relatorio_multas` |
| Estatísticas com `reduce` | `contar_livros_por_categoria`, `contar_emprestimos_por_usuario`, `calcular_valor_total_multas` |
| Comparação de paradigmas | `total_multas_imperativo` x `total_multas_funcional` |

Funções puras: `filtrar_livros_por_categoria`, `calcular_multa`, `filtrar_emprestimos_ativos`, `filtrar_emprestimos_atrasados`, `criar_item_multa`, `somar_valores`, `gerar_relatorio_multas`, as funções de contagem, `gerar_estatisticas` e as de formatação.

Imutabilidade: `Livro`, `Usuario` e `Emprestimo` não possuem métodos que alterem seu estado. A devolução cria um novo `Emprestimo` (`com_devolucao`) que substitui o anterior dentro da `Biblioteca`. Relatórios e estatísticas são `dataclass` congeladas, com tuplas e `MappingProxyType`. As funções puras sempre devolvem estruturas novas.

Separação: efeitos colaterais ficam em `Biblioteca` (cadastros, empréstimos, devoluções) e em `main.py` (impressão). Os cálculos ficam em `funcoes_puras.py`.

## Regras de negócio

- Cada livro é um exemplar único; a disponibilidade é derivada da existência de empréstimo ativo para ele.
- Um livro não pode estar em dois empréstimos ativos. A verificação e o registro ocorrem sob uma trava (`threading.RLock`), de modo que dois pedidos simultâneos não conseguem emprestar o mesmo livro.
- Empréstimo atrasado: ativo e com data de referência posterior à data prevista.
- Multa: R$ 2,00 por dia de atraso, apenas para empréstimos ativos e atrasados. Valores monetários usam `Decimal`.
