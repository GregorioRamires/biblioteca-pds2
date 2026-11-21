"""Acesso ao banco de dados SQLite.

Cada requisição HTTP usa uma única conexão, guardada no objeto ``g`` do Flask
e fechada automaticamente ao final da requisição.
"""

import sqlite3
from pathlib import Path

from flask import abort, current_app, g


def get_db():
    """Devolve a conexão da requisição atual, abrindo-a se necessário."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
        # O SQLite só valida chaves estrangeiras se isso for ligado por conexão.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria as tabelas (se ainda não existirem) a partir do schema.sql."""
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)


def buscar_ou_404(sql, parametros=()):
    """Executa uma consulta que deve devolver um registro; senão, erro 404."""
    linha = get_db().execute(sql, parametros).fetchone()
    if linha is None:
        abort(404)
    return linha


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
