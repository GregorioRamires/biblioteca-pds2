"""Sistema de Gerenciamento de Biblioteca — fábrica da aplicação Flask."""

import os
from datetime import date

from flask import Flask, render_template

from . import db

# Rótulos exibidos para cada situação de empréstimo.
SITUACOES = {
    "no_prazo": "No prazo",
    "atrasado": "Atrasado",
    "devolvido": "Devolvido",
}


def data_br(valor):
    """Converte 'AAAA-MM-DD' (formato gravado no banco) para 'DD/MM/AAAA'."""
    if not valor:
        return "—"
    return date.fromisoformat(valor).strftime("%d/%m/%Y")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "chave-de-desenvolvimento"),
        DATABASE=os.path.join(app.instance_path, "biblioteca.sqlite"),
        PRAZO_DIAS=14,          # prazo padrão de devolução
        LIMITE_EMPRESTIMOS=3,   # máximo de empréstimos em aberto por leitor
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    app.jinja_env.filters["data_br"] = data_br
    app.jinja_env.globals["SITUACOES"] = SITUACOES

    from . import categorias, emprestimos, leitores, livros, painel

    app.register_blueprint(painel.bp)
    app.register_blueprint(categorias.bp)
    app.register_blueprint(livros.bp)
    app.register_blueprint(leitores.bp)
    app.register_blueprint(emprestimos.bp)

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("404.html"), 404

    return app
