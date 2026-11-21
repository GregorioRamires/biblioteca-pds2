-- Esquema do banco de dados do Sistema de Biblioteca (SQLite).
-- Executado automaticamente quando a aplicação inicia; o IF NOT EXISTS
-- garante que os dados já gravados não sejam apagados.

CREATE TABLE IF NOT EXISTS categoria (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS livro (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo         TEXT    NOT NULL,
    autor          TEXT    NOT NULL,
    isbn           TEXT    UNIQUE,
    ano_publicacao INTEGER,
    quantidade     INTEGER NOT NULL DEFAULT 1 CHECK (quantidade >= 0),
    categoria_id   INTEGER NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categoria (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS leitor (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    telefone      TEXT,
    data_cadastro TEXT NOT NULL
);

-- A situação do empréstimo (no prazo, atrasado, devolvido) não é gravada:
-- ela é calculada a partir das datas, evitando informação redundante.
CREATE TABLE IF NOT EXISTS emprestimo (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    livro_id        INTEGER NOT NULL,
    leitor_id       INTEGER NOT NULL,
    data_emprestimo TEXT    NOT NULL,
    data_prevista   TEXT    NOT NULL,
    data_devolucao  TEXT,
    CHECK (data_prevista >= data_emprestimo),
    FOREIGN KEY (livro_id)  REFERENCES livro (id)  ON DELETE RESTRICT,
    FOREIGN KEY (leitor_id) REFERENCES leitor (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_livro_categoria    ON livro (categoria_id);
CREATE INDEX IF NOT EXISTS idx_emprestimo_livro   ON emprestimo (livro_id);
CREATE INDEX IF NOT EXISTS idx_emprestimo_leitor  ON emprestimo (leitor_id);
