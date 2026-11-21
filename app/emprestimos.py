"""Empréstimos e devoluções de livros."""

from datetime import date, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from .db import buscar_ou_404, get_db
from .livros import SQL_LIVROS

bp = Blueprint("emprestimos", __name__, url_prefix="/emprestimos")

# A situação é calculada na consulta, a partir das datas:
#   devolvido -> já tem data de devolução
#   atrasado  -> não devolvido e a data prevista já passou
#   no_prazo  -> não devolvido e ainda dentro do prazo
SQL_EMPRESTIMOS = """
    SELECT e.*, l.titulo AS livro, r.nome AS leitor,
           CASE
               WHEN e.data_devolucao IS NOT NULL THEN 'devolvido'
               WHEN e.data_prevista < :hoje THEN 'atrasado'
               ELSE 'no_prazo'
           END AS situacao
    FROM emprestimo e
    JOIN livro l ON l.id = e.livro_id
    JOIN leitor r ON r.id = e.leitor_id
"""


def hoje():
    return date.today().isoformat()


def _ler_data(texto):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def _opcoes_formulario():
    db = get_db()
    livros = db.execute(
        f"SELECT * FROM ({SQL_LIVROS}) WHERE disponiveis > 0 ORDER BY titulo"
    ).fetchall()
    leitores = db.execute("SELECT id, nome FROM leitor ORDER BY nome").fetchall()
    return livros, leitores


def _validar_novo(form):
    """Valida o formulário e aplica as regras de negócio do empréstimo."""
    db = get_db()
    dados = {
        "livro_id": form.get("livro_id", "").strip(),
        "leitor_id": form.get("leitor_id", "").strip(),
        "data_emprestimo": form.get("data_emprestimo", "").strip(),
        "data_prevista": form.get("data_prevista", "").strip(),
    }
    erros = []

    livro = None
    if dados["livro_id"].isdigit():
        livro = db.execute(
            f"SELECT * FROM ({SQL_LIVROS}) WHERE id = ?", (dados["livro_id"],)
        ).fetchone()
    if livro is None:
        erros.append("Selecione um livro válido.")
    elif livro["disponiveis"] < 1:
        erros.append(f"Não há exemplares disponíveis de “{livro['titulo']}”.")

    leitor = None
    if dados["leitor_id"].isdigit():
        leitor = db.execute("SELECT * FROM leitor WHERE id = ?", (dados["leitor_id"],)).fetchone()
    if leitor is None:
        erros.append("Selecione um leitor válido.")
    else:
        abertos = db.execute(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(data_prevista < ?), 0) AS atrasados
            FROM emprestimo
            WHERE leitor_id = ? AND data_devolucao IS NULL
            """,
            (hoje(), leitor["id"]),
        ).fetchone()
        limite = current_app.config["LIMITE_EMPRESTIMOS"]
        if abertos["atrasados"] > 0:
            erros.append("Este leitor possui empréstimo em atraso e não pode pegar outro livro.")
        elif abertos["total"] >= limite:
            erros.append(f"Este leitor já atingiu o limite de {limite} empréstimos em aberto.")

    data_emprestimo = _ler_data(dados["data_emprestimo"])
    data_prevista = _ler_data(dados["data_prevista"])
    if data_emprestimo is None:
        erros.append("Informe uma data de empréstimo válida.")
    elif data_emprestimo > date.today():
        erros.append("A data de empréstimo não pode ser futura.")
    if data_prevista is None:
        erros.append("Informe uma data prevista de devolução válida.")
    elif data_emprestimo and data_prevista < data_emprestimo:
        erros.append("A data prevista de devolução não pode ser anterior à data do empréstimo.")

    return dados, erros


@bp.route("/")
def listar():
    situacao = request.args.get("situacao", "")
    sql = f"SELECT * FROM ({SQL_EMPRESTIMOS})"
    parametros = {"hoje": hoje()}
    if situacao in ("no_prazo", "atrasado", "devolvido"):
        sql += " WHERE situacao = :situacao"
        parametros["situacao"] = situacao
    else:
        situacao = ""
    sql += " ORDER BY data_devolucao IS NOT NULL, data_prevista, id"
    emprestimos = get_db().execute(sql, parametros).fetchall()
    return render_template("emprestimos/lista.html", emprestimos=emprestimos, situacao=situacao)


@bp.route("/novo", methods=("GET", "POST"))
def criar():
    livros, leitores = _opcoes_formulario()
    prazo = current_app.config["PRAZO_DIAS"]
    dados = {
        "livro_id": "",
        "leitor_id": "",
        "data_emprestimo": hoje(),
        "data_prevista": (date.today() + timedelta(days=prazo)).isoformat(),
    }
    if request.method == "POST":
        dados, erros = _validar_novo(request.form)
        if not erros:
            db = get_db()
            db.execute(
                """
                INSERT INTO emprestimo (livro_id, leitor_id, data_emprestimo, data_prevista)
                VALUES (?, ?, ?, ?)
                """,
                (int(dados["livro_id"]), int(dados["leitor_id"]),
                 dados["data_emprestimo"], dados["data_prevista"]),
            )
            db.commit()
            flash("Empréstimo registrado com sucesso.", "sucesso")
            return redirect(url_for("emprestimos.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template(
        "emprestimos/form.html", emprestimo=dados, livros=livros, leitores=leitores, prazo=prazo
    )


@bp.route("/<int:id>/renovar", methods=("GET", "POST"))
def renovar(id):
    """Altera a data prevista de devolução de um empréstimo ainda não devolvido."""
    emprestimo = buscar_ou_404(
        f"SELECT * FROM ({SQL_EMPRESTIMOS}) WHERE id = :id", {"hoje": hoje(), "id": id}
    )
    if emprestimo["data_devolucao"]:
        flash("Este empréstimo já foi devolvido e não pode ser alterado.", "erro")
        return redirect(url_for("emprestimos.listar"))

    nova_data = emprestimo["data_prevista"]
    if request.method == "POST":
        nova_data = request.form.get("data_prevista", "").strip()
        data = _ler_data(nova_data)
        if data is None:
            flash("Informe uma data prevista de devolução válida.", "erro")
        elif data.isoformat() < emprestimo["data_emprestimo"]:
            flash("A data prevista de devolução não pode ser anterior à data do empréstimo.", "erro")
        else:
            db = get_db()
            db.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?", (data.isoformat(), id))
            db.commit()
            flash("Data de devolução atualizada.", "sucesso")
            return redirect(url_for("emprestimos.listar"))
    return render_template("emprestimos/renovar.html", emprestimo=emprestimo, nova_data=nova_data)


@bp.route("/<int:id>/devolver", methods=("POST",))
def devolver(id):
    emprestimo = buscar_ou_404("SELECT * FROM emprestimo WHERE id = ?", (id,))
    if emprestimo["data_devolucao"]:
        flash("Este empréstimo já havia sido devolvido.", "erro")
    else:
        db = get_db()
        db.execute("UPDATE emprestimo SET data_devolucao = ? WHERE id = ?", (hoje(), id))
        db.commit()
        flash("Devolução registrada. O exemplar voltou a ficar disponível.", "sucesso")
    return redirect(request.referrer or url_for("emprestimos.listar"))


@bp.route("/<int:id>/excluir", methods=("POST",))
def excluir(id):
    buscar_ou_404("SELECT id FROM emprestimo WHERE id = ?", (id,))
    db = get_db()
    db.execute("DELETE FROM emprestimo WHERE id = ?", (id,))
    db.commit()
    flash("Registro de empréstimo excluído.", "sucesso")
    return redirect(url_for("emprestimos.listar"))
