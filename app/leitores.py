"""CRUD de leitores (pessoas que pegam livros emprestados)."""

import re
import sqlite3
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import buscar_ou_404, get_db

bp = Blueprint("leitores", __name__, url_prefix="/leitores")

EMAIL_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validar(form):
    dados = {
        "nome": form.get("nome", "").strip(),
        "email": form.get("email", "").strip(),
        "telefone": form.get("telefone", "").strip(),
    }
    erros = []
    if not dados["nome"]:
        erros.append("Informe o nome do leitor.")
    if not EMAIL_VALIDO.match(dados["email"]):
        erros.append("Informe um e-mail válido.")
    if dados["telefone"] and len(re.sub(r"\D", "", dados["telefone"])) not in (10, 11):
        erros.append("O telefone deve ter 10 ou 11 dígitos (com DDD).")
    return dados, erros


@bp.route("/")
def listar():
    busca = request.args.get("q", "").strip()
    sql = """
        SELECT r.*, (
            SELECT COUNT(*) FROM emprestimo e
            WHERE e.leitor_id = r.id AND e.data_devolucao IS NULL
        ) AS em_aberto
        FROM leitor r
    """
    parametros = []
    if busca:
        sql += " WHERE r.nome LIKE ? OR r.email LIKE ?"
        parametros = [f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY r.nome"
    leitores = get_db().execute(sql, parametros).fetchall()
    return render_template("leitores/lista.html", leitores=leitores, busca=busca)


@bp.route("/novo", methods=("GET", "POST"))
def criar():
    dados = {"nome": "", "email": "", "telefone": ""}
    if request.method == "POST":
        dados, erros = _validar(request.form)
        if not erros:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO leitor (nome, email, telefone, data_cadastro) VALUES (?, ?, ?, ?)",
                    (dados["nome"], dados["email"], dados["telefone"] or None, date.today().isoformat()),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erros.append("Já existe um leitor cadastrado com esse e-mail.")
            else:
                flash("Leitor cadastrado com sucesso.", "sucesso")
                return redirect(url_for("leitores.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template("leitores/form.html", leitor=dados, titulo="Novo leitor")


@bp.route("/<int:id>/editar", methods=("GET", "POST"))
def editar(id):
    dados = dict(buscar_ou_404("SELECT * FROM leitor WHERE id = ?", (id,)))
    if request.method == "POST":
        dados, erros = _validar(request.form)
        if not erros:
            db = get_db()
            try:
                db.execute(
                    "UPDATE leitor SET nome = ?, email = ?, telefone = ? WHERE id = ?",
                    (dados["nome"], dados["email"], dados["telefone"] or None, id),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erros.append("Já existe um leitor cadastrado com esse e-mail.")
            else:
                flash("Leitor atualizado com sucesso.", "sucesso")
                return redirect(url_for("leitores.listar"))
        for erro in erros:
            flash(erro, "erro")
    return render_template("leitores/form.html", leitor=dados, titulo="Editar leitor")


@bp.route("/<int:id>/excluir", methods=("POST",))
def excluir(id):
    buscar_ou_404("SELECT id FROM leitor WHERE id = ?", (id,))
    db = get_db()
    try:
        db.execute("DELETE FROM leitor WHERE id = ?", (id,))
        db.commit()
    except sqlite3.IntegrityError:
        flash("Não é possível excluir: existem empréstimos registrados para este leitor.", "erro")
    else:
        flash("Leitor excluído.", "sucesso")
    return redirect(url_for("leitores.listar"))
