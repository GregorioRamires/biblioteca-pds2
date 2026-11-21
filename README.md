# Sistema de Gerenciamento de Biblioteca

Projeto da disciplina **Projeto de Desenvolvimento de Software II** (UniFil).

Aplicação web para controlar o acervo e os empréstimos de uma biblioteca de pequeno porte:
cadastro de categorias, livros e leitores, registro de empréstimos, devoluções e renovações,
e um painel com os empréstimos em atraso.

- **Autor:** Gregorio Alvares Ramires (trabalho individual)
- **Documentação:** [docs/Documentacao.pdf](docs/Documentacao.pdf)

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python 3.12 | Linguagem da aplicação |
| Flask 3 | Framework web (rotas e requisições) |
| SQLite 3 | Banco de dados relacional (módulo `sqlite3`, SQL escrito à mão) |
| Jinja2 + HTML/CSS | Telas do sistema |
| unittest | Testes automatizados |

## Como executar (Windows)

Pré-requisito: [Python 3.10 ou superior](https://www.python.org/downloads/).

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py     # opcional: insere dados de exemplo
python run.py
```

Depois, abra <http://localhost:5000> no navegador. O banco de dados é criado automaticamente
em `instance/biblioteca.sqlite` na primeira execução.

## Testes

```powershell
python -m unittest discover -s tests -v
```

## Funcionalidades

| Entidade | Criar | Consultar | Atualizar | Excluir |
| --- | :-: | :-: | :-: | :-: |
| Categorias | ✔ | ✔ | ✔ | ✔ |
| Livros | ✔ | ✔ (busca e filtro) | ✔ | ✔ |
| Leitores | ✔ | ✔ (busca) | ✔ | ✔ |
| Empréstimos | ✔ | ✔ (filtro por situação) | ✔ (devolução e renovação) | ✔ |

Regras de negócio implementadas:

- um livro só é emprestado se houver exemplar disponível;
- leitor com empréstimo em atraso não pode pegar outro livro;
- cada leitor pode ter no máximo 3 empréstimos em aberto;
- prazo padrão de devolução de 14 dias, com possibilidade de renovação;
- não é possível excluir categoria com livros, nem livro ou leitor com empréstimos registrados.

## Estrutura do projeto

```
run.py              inicia o servidor
seed.py             insere dados de exemplo
app/
  __init__.py       cria e configura a aplicação Flask
  db.py             conexão com o banco de dados
  schema.sql        criação das tabelas
  categorias.py     CRUD de categorias
  livros.py         CRUD de livros
  leitores.py       CRUD de leitores
  emprestimos.py    empréstimo, devolução e renovação
  painel.py         painel inicial
  templates/        páginas HTML (Jinja2)
  static/           folha de estilo
tests/              testes automatizados
docs/               documentação (PDF) e script que a gera
```
