"""Painel inicial: resumo do acervo e empréstimos que precisam de atenção."""

from flask import Blueprint, render_template

from .db import get_db
from .emprestimos import SQL_EMPRESTIMOS, hoje

bp = Blueprint("painel", __name__)


@bp.route("/")
def index():
    db = get_db()
    parametros = {"hoje": hoje()}
    resumo = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM livro) AS titulos,
            (SELECT COALESCE(SUM(quantidade), 0) FROM livro) AS exemplares,
            (SELECT COUNT(*) FROM leitor) AS leitores,
            (SELECT COUNT(*) FROM emprestimo WHERE data_devolucao IS NULL) AS em_aberto,
            (SELECT COUNT(*) FROM emprestimo
             WHERE data_devolucao IS NULL AND data_prevista < :hoje) AS atrasados
        """,
        parametros,
    ).fetchone()
    atrasados = db.execute(
        f"SELECT * FROM ({SQL_EMPRESTIMOS}) WHERE situacao = 'atrasado' ORDER BY data_prevista",
        parametros,
    ).fetchall()
    recentes = db.execute(
        f"SELECT * FROM ({SQL_EMPRESTIMOS}) ORDER BY data_emprestimo DESC, id DESC LIMIT 5",
        parametros,
    ).fetchall()
    return render_template("painel.html", resumo=resumo, atrasados=atrasados, recentes=recentes)
