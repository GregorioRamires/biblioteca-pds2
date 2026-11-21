"""Popula o banco com dados de exemplo: python seed.py

Só insere dados se o banco estiver vazio, para não duplicar registros.
"""

from datetime import date, timedelta

from app import create_app
from app.db import get_db

CATEGORIAS = [
    ("Romance", "Narrativas longas de ficção"),
    ("Tecnologia", "Programação, banco de dados e engenharia de software"),
    ("Ficção científica", "Histórias baseadas em ciência e futuro"),
    ("História", "Obras sobre fatos e períodos históricos"),
]

LIVROS = [
    ("Dom Casmurro", "Machado de Assis", "9788535910663", 1899, 3, "Romance"),
    ("Capitães da Areia", "Jorge Amado", "9788535914061", 1937, 2, "Romance"),
    ("Engenharia de Software", "Ian Sommerville", "9788543024974", 2018, 2, "Tecnologia"),
    ("Sistemas de Banco de Dados", "Elmasri e Navathe", "9788543025001", 2018, 1, "Tecnologia"),
    ("Código Limpo", "Robert C. Martin", "9788576082675", 2009, 2, "Tecnologia"),
    ("Fundação", "Isaac Asimov", "9788576570660", 1951, 2, "Ficção científica"),
    ("Duna", "Frank Herbert", "9788576573135", 1965, 1, "Ficção científica"),
    ("Sapiens", "Yuval Noah Harari", "9788525432186", 2011, 2, "História"),
]

LEITORES = [
    ("Ana Beatriz Souza", "ana.souza@example.com", "(43) 99911-2233"),
    ("Carlos Eduardo Lima", "carlos.lima@example.com", "(43) 99822-3344"),
    ("Mariana Oliveira", "mariana.oliveira@example.com", "(43) 99733-4455"),
    ("Rafael Martins", "rafael.martins@example.com", None),
]


def popular():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM categoria").fetchone()[0]:
        print("O banco já possui dados; nada foi inserido.")
        return

    hoje = date.today()

    def dia(deslocamento):
        return (hoje + timedelta(days=deslocamento)).isoformat()

    db.executemany("INSERT INTO categoria (nome, descricao) VALUES (?, ?)", CATEGORIAS)
    categorias = {linha["nome"]: linha["id"] for linha in db.execute("SELECT id, nome FROM categoria")}

    db.executemany(
        "INSERT INTO livro (titulo, autor, isbn, ano_publicacao, quantidade, categoria_id) VALUES (?, ?, ?, ?, ?, ?)",
        [(t, a, i, ano, q, categorias[c]) for t, a, i, ano, q, c in LIVROS],
    )
    db.executemany(
        "INSERT INTO leitor (nome, email, telefone, data_cadastro) VALUES (?, ?, ?, ?)",
        [(n, e, t, dia(-60)) for n, e, t in LEITORES],
    )

    livros = {linha["titulo"]: linha["id"] for linha in db.execute("SELECT id, titulo FROM livro")}
    leitores = {linha["nome"]: linha["id"] for linha in db.execute("SELECT id, nome FROM leitor")}

    # (livro, leitor, emprestado há N dias, prazo em relação a hoje, devolvido há N dias ou None)
    emprestimos = [
        ("Dom Casmurro", "Ana Beatriz Souza", -5, 9, None),               # no prazo
        ("Código Limpo", "Ana Beatriz Souza", -2, 12, None),              # no prazo
        ("Duna", "Carlos Eduardo Lima", -20, -6, None),                   # atrasado
        ("Sapiens", "Mariana Oliveira", -30, -16, -18),                   # devolvido
        ("Fundação", "Rafael Martins", -12, 2, -3),                       # devolvido
    ]
    db.executemany(
        """
        INSERT INTO emprestimo (livro_id, leitor_id, data_emprestimo, data_prevista, data_devolucao)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (livros[l], leitores[r], dia(inicio), dia(prazo), dia(dev) if dev is not None else None)
            for l, r, inicio, prazo, dev in emprestimos
        ],
    )
    db.commit()
    print("Dados de exemplo inseridos com sucesso.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        popular()
