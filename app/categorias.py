"""CRUD de categorias de livros."""

import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import buscar_ou_404, get_db

bp = Blueprint("categorias", __name__, url_prefix="/categorias")


def _validar(form):
    dados = {
        "nome": form.get("nome", "").strip(),
        "descricao": form.get("descricao", "").strip(),
    }
    erros = []
    if not dados["nome"]:
        erros.append("Informe o nome da categoria.")
    elif len(dados["nome"]) > 60:
        erros.append("O nome da categoria deve ter no máximo 60 caracteres.")
    return dados, erros


@bp.route("/")
def listar():
    categorias = get_db().execute(
        """
        SELECT c.id, c.nome, c.descricao, COUNT(l.id) AS total_livros
        FROM categoria c
        LEFT JOIN livro l ON l.categoria_id = c.id
        GROUP BY c.id
        ORDER BY c.nome
        """
    ).fetchall()
    return render_template("categorias/lista.html", categorias=categorias)


@bp.route("/nova", methods=("GET", "POST"))
def criar():
    dados = {"nome": "", "descricao": ""}
    if request.method == "POST":
        dados, erros = _validar(request.form)
        if not erros:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO categoria (nome, descricao) VALUES (?, ?)",
                    (dados["nome"], dados["descricao"] or None),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erros.append("Já existe uma categoria com esse nome.")
            else:
                flash("Categoria cadastrada com sucesso.", "sucesso")
                return redirect(url_for("categorias.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template("categorias/form.html", categoria=dados, titulo="Nova categoria")


@bp.route("/<int:id>/editar", methods=("GET", "POST"))
def editar(id):
    dados = dict(buscar_ou_404("SELECT * FROM categoria WHERE id = ?", (id,)))
    if request.method == "POST":
        dados, erros = _validar(request.form)
        if not erros:
            db = get_db()
            try:
                db.execute(
                    "UPDATE categoria SET nome = ?, descricao = ? WHERE id = ?",
                    (dados["nome"], dados["descricao"] or None, id),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erros.append("Já existe uma categoria com esse nome.")
            else:
                flash("Categoria atualizada com sucesso.", "sucesso")
                return redirect(url_for("categorias.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template("categorias/form.html", categoria=dados, titulo="Editar categoria")


@bp.route("/<int:id>/excluir", methods=("POST",))
def excluir(id):
    buscar_ou_404("SELECT id FROM categoria WHERE id = ?", (id,))
    db = get_db()
    try:
        db.execute("DELETE FROM categoria WHERE id = ?", (id,))
        db.commit()
    except sqlite3.IntegrityError:
        # A chave estrangeira (ON DELETE RESTRICT) impede a exclusão.
        flash("Não é possível excluir: existem livros nesta categoria.", "erro")
    else:
        flash("Categoria excluída.", "sucesso")
    return redirect(url_for("categorias.listar"))
