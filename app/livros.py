"""CRUD de livros do acervo."""

import sqlite3
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import buscar_ou_404, get_db

bp = Blueprint("livros", __name__, url_prefix="/livros")

# "disponiveis" = exemplares cadastrados menos os que estão emprestados agora.
SQL_LIVROS = """
    SELECT l.*, c.nome AS categoria,
           l.quantidade - (
               SELECT COUNT(*) FROM emprestimo e
               WHERE e.livro_id = l.id AND e.data_devolucao IS NULL
           ) AS disponiveis
    FROM livro l
    JOIN categoria c ON c.id = l.categoria_id
"""


def _categorias():
    return get_db().execute("SELECT id, nome FROM categoria ORDER BY nome").fetchall()


def _emprestados(livro_id):
    return get_db().execute(
        "SELECT COUNT(*) FROM emprestimo WHERE livro_id = ? AND data_devolucao IS NULL",
        (livro_id,),
    ).fetchone()[0]


def _validar(form, livro_id=None):
    dados = {
        "titulo": form.get("titulo", "").strip(),
        "autor": form.get("autor", "").strip(),
        "isbn": form.get("isbn", "").strip(),
        "ano_publicacao": form.get("ano_publicacao", "").strip(),
        "quantidade": form.get("quantidade", "").strip(),
        "categoria_id": form.get("categoria_id", "").strip(),
    }
    erros = []

    if not dados["titulo"]:
        erros.append("Informe o título do livro.")
    if not dados["autor"]:
        erros.append("Informe o autor do livro.")

    if dados["ano_publicacao"]:
        ano_atual = date.today().year
        if not dados["ano_publicacao"].isdigit() or not 1000 <= int(dados["ano_publicacao"]) <= ano_atual:
            erros.append(f"O ano de publicação deve estar entre 1000 e {ano_atual}.")

    if not dados["quantidade"].isdigit() or int(dados["quantidade"]) < 1:
        erros.append("A quantidade de exemplares deve ser um número inteiro maior que zero.")
    elif livro_id is not None:
        emprestados = _emprestados(livro_id)
        if int(dados["quantidade"]) < emprestados:
            erros.append(
                f"A quantidade não pode ser menor que {emprestados}, "
                "pois esse é o número de exemplares emprestados no momento."
            )

    categoria = None
    if dados["categoria_id"].isdigit():
        categoria = get_db().execute(
            "SELECT id FROM categoria WHERE id = ?", (dados["categoria_id"],)
        ).fetchone()
    if categoria is None:
        erros.append("Selecione uma categoria válida.")

    return dados, erros


def _parametros(dados):
    return (
        dados["titulo"],
        dados["autor"],
        dados["isbn"] or None,
        int(dados["ano_publicacao"]) if dados["ano_publicacao"] else None,
        int(dados["quantidade"]),
        int(dados["categoria_id"]),
    )


@bp.route("/")
def listar():
    busca = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", "").strip()

    sql = SQL_LIVROS + " WHERE 1 = 1"
    parametros = []
    if busca:
        sql += " AND (l.titulo LIKE ? OR l.autor LIKE ?)"
        parametros += [f"%{busca}%", f"%{busca}%"]
    if categoria_id.isdigit():
        sql += " AND l.categoria_id = ?"
        parametros.append(int(categoria_id))
    sql += " ORDER BY l.titulo"

    livros = get_db().execute(sql, parametros).fetchall()
    return render_template(
        "livros/lista.html",
        livros=livros,
        categorias=_categorias(),
        busca=busca,
        categoria_id=categoria_id,
    )


@bp.route("/novo", methods=("GET", "POST"))
def criar():
    categorias = _categorias()
    if not categorias:
        flash("Cadastre uma categoria antes de cadastrar livros.", "erro")
        return redirect(url_for("categorias.criar"))

    dados = {"titulo": "", "autor": "", "isbn": "", "ano_publicacao": "",
             "quantidade": "1", "categoria_id": ""}
    if request.method == "POST":
        dados, erros = _validar(request.form)
        if not erros:
            db = get_db()
            try:
                db.execute(
                    """
                    INSERT INTO livro (titulo, autor, isbn, ano_publicacao, quantidade, categoria_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    _parametros(dados),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erros.append("Já existe um livro cadastrado com esse ISBN.")
            else:
                flash("Livro cadastrado com sucesso.", "sucesso")
                return redirect(url_for("livros.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template("livros/form.html", livro=dados, categorias=categorias, titulo="Novo livro")


@bp.route("/<int:id>/editar", methods=("GET", "POST"))
def editar(id):
    dados = dict(buscar_ou_404("SELECT * FROM livro WHERE id = ?", (id,)))
    if request.method == "POST":
        dados, erros = _validar(request.form, livro_id=id)
        if not erros:
            db = get_db()
            try:
                db.execute(
                    """
                    UPDATE livro
                    SET titulo = ?, autor = ?, isbn = ?, ano_publicacao = ?,
                        quantidade = ?, categoria_id = ?
                    WHERE id = ?
                    """,
                    _parametros(dados) + (id,),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erros.append("Já existe um livro cadastrado com esse ISBN.")
            else:
                flash("Livro atualizado com sucesso.", "sucesso")
                return redirect(url_for("livros.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template("livros/form.html", livro=dados, categorias=_categorias(), titulo="Editar livro")


@bp.route("/<int:id>/excluir", methods=("POST",))
def excluir(id):
    buscar_ou_404("SELECT id FROM livro WHERE id = ?", (id,))
    db = get_db()
    try:
        db.execute("DELETE FROM livro WHERE id = ?", (id,))
        db.commit()
    except sqlite3.IntegrityError:
        flash("Não é possível excluir: existem empréstimos registrados para este livro.", "erro")
    else:
        flash("Livro excluído.", "sucesso")
    return redirect(url_for("livros.listar"))
