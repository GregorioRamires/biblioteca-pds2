"""Testes automatizados: python -m unittest discover -s tests -v

Cada teste roda com um banco SQLite temporário, criado do zero.
"""

import os
import tempfile
import unittest
from datetime import date, timedelta

from app import create_app
from app.db import get_db


def dia(deslocamento=0):
    return (date.today() + timedelta(days=deslocamento)).isoformat()


class BibliotecaTestCase(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "DATABASE": os.path.join(self.pasta.name, "teste.sqlite"),
        })
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.pasta.cleanup()

    # ---------- utilitários ----------
    def post(self, url, **dados):
        return self.cliente.post(url, data=dados, follow_redirects=True)

    def texto(self, resposta):
        return resposta.get_data(as_text=True)

    def contar(self, tabela):
        with self.app.app_context():
            return get_db().execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]

    def criar_base(self, quantidade="1"):
        """Cria uma categoria, um livro e um leitor (todos com id 1)."""
        self.post("/categorias/nova", nome="Romance", descricao="")
        self.post("/livros/novo", titulo="Dom Casmurro", autor="Machado de Assis", isbn="111",
                  ano_publicacao="1899", quantidade=quantidade, categoria_id="1")
        self.post("/leitores/novo", nome="Ana Souza", email="ana@example.com", telefone="")

    def emprestar(self, livro_id="1", leitor_id="1", inicio=0, prazo=14):
        return self.post("/emprestimos/novo", livro_id=livro_id, leitor_id=leitor_id,
                         data_emprestimo=dia(inicio), data_prevista=dia(prazo))

    # ---------- categorias ----------
    def test_crud_de_categoria(self):
        r = self.post("/categorias/nova", nome="Tecnologia", descricao="Livros de TI")
        self.assertIn("Categoria cadastrada com sucesso", self.texto(r))
        self.assertIn("Tecnologia", self.texto(self.cliente.get("/categorias/")))

        r = self.post("/categorias/1/editar", nome="Informática", descricao="")
        self.assertIn("Informática", self.texto(r))

        r = self.post("/categorias/1/excluir")
        self.assertIn("Categoria excluída", self.texto(r))
        self.assertEqual(self.contar("categoria"), 0)

    def test_categoria_com_nome_repetido_e_recusada(self):
        self.post("/categorias/nova", nome="Romance", descricao="")
        r = self.post("/categorias/nova", nome="romance", descricao="")
        self.assertIn("Já existe uma categoria com esse nome", self.texto(r))
        self.assertEqual(self.contar("categoria"), 1)

    def test_categoria_com_livros_nao_pode_ser_excluida(self):
        self.criar_base()
        r = self.post("/categorias/1/excluir")
        self.assertIn("existem livros nesta categoria", self.texto(r))
        self.assertEqual(self.contar("categoria"), 1)

    # ---------- livros ----------
    def test_crud_de_livro(self):
        self.criar_base()
        self.assertIn("Dom Casmurro", self.texto(self.cliente.get("/livros/")))

        r = self.post("/livros/1/editar", titulo="Dom Casmurro (ed. especial)", autor="Machado de Assis",
                      isbn="111", ano_publicacao="1899", quantidade="2", categoria_id="1")
        self.assertIn("Livro atualizado com sucesso", self.texto(r))
        self.assertIn("ed. especial", self.texto(r))

        r = self.post("/livros/1/excluir")
        self.assertIn("Livro excluído", self.texto(r))
        self.assertEqual(self.contar("livro"), 0)

    def test_livro_invalido_nao_e_gravado(self):
        self.post("/categorias/nova", nome="Romance", descricao="")
        r = self.post("/livros/novo", titulo="", autor="", isbn="", ano_publicacao="3000",
                      quantidade="0", categoria_id="99")
        pagina = self.texto(r)
        self.assertIn("Informe o título do livro", pagina)
        self.assertIn("O ano de publicação deve estar entre", pagina)
        self.assertIn("maior que zero", pagina)
        self.assertIn("Selecione uma categoria válida", pagina)
        self.assertEqual(self.contar("livro"), 0)

    def test_busca_de_livros(self):
        self.criar_base()
        self.post("/livros/novo", titulo="Fundação", autor="Isaac Asimov", isbn="222",
                  ano_publicacao="1951", quantidade="1", categoria_id="1")
        pagina = self.texto(self.cliente.get("/livros/?q=asimov"))
        self.assertIn("Fundação", pagina)
        self.assertNotIn("Dom Casmurro", pagina)

    # ---------- leitores ----------
    def test_crud_de_leitor(self):
        r = self.post("/leitores/novo", nome="Ana Souza", email="ana@example.com", telefone="(43) 99911-2233")
        self.assertIn("Leitor cadastrado com sucesso", self.texto(r))

        r = self.post("/leitores/1/editar", nome="Ana Beatriz Souza", email="ana@example.com", telefone="")
        self.assertIn("Ana Beatriz Souza", self.texto(r))

        r = self.post("/leitores/1/excluir")
        self.assertIn("Leitor excluído", self.texto(r))
        self.assertEqual(self.contar("leitor"), 0)

    def test_email_de_leitor_deve_ser_valido_e_unico(self):
        r = self.post("/leitores/novo", nome="Ana", email="sem-arroba", telefone="")
        self.assertIn("Informe um e-mail válido", self.texto(r))

        self.post("/leitores/novo", nome="Ana", email="ana@example.com", telefone="")
        r = self.post("/leitores/novo", nome="Outra Ana", email="ANA@example.com", telefone="")
        self.assertIn("Já existe um leitor cadastrado com esse e-mail", self.texto(r))
        self.assertEqual(self.contar("leitor"), 1)

    # ---------- empréstimos ----------
    def test_emprestimo_e_devolucao(self):
        self.criar_base()
        r = self.emprestar()
        self.assertIn("Empréstimo registrado com sucesso", self.texto(r))
        self.assertIn("0 de 1", self.texto(self.cliente.get("/livros/")))

        r = self.post("/emprestimos/1/devolver")
        self.assertIn("Devolução registrada", self.texto(r))
        self.assertIn("1 de 1", self.texto(self.cliente.get("/livros/")))
        self.assertIn("Devolvido", self.texto(self.cliente.get("/emprestimos/?situacao=devolvido")))

    def test_nao_empresta_livro_sem_exemplar_disponivel(self):
        self.criar_base(quantidade="1")
        self.post("/leitores/novo", nome="Carlos Lima", email="carlos@example.com", telefone="")
        self.emprestar(leitor_id="1")
        r = self.emprestar(leitor_id="2")
        self.assertIn("Não há exemplares disponíveis", self.texto(r))
        self.assertEqual(self.contar("emprestimo"), 1)

    def test_leitor_com_atraso_nao_pega_outro_livro(self):
        self.criar_base(quantidade="5")
        self.emprestar(inicio=-20, prazo=-5)  # já está atrasado
        self.assertIn("Atrasado", self.texto(self.cliente.get("/emprestimos/?situacao=atrasado")))
        r = self.emprestar()
        self.assertIn("possui empréstimo em atraso", self.texto(r))
        self.assertEqual(self.contar("emprestimo"), 1)

    def test_limite_de_emprestimos_por_leitor(self):
        self.criar_base(quantidade="10")
        for _ in range(3):
            self.emprestar()
        r = self.emprestar()
        self.assertIn("já atingiu o limite de 3 empréstimos", self.texto(r))
        self.assertEqual(self.contar("emprestimo"), 3)

    def test_datas_invalidas_no_emprestimo(self):
        self.criar_base()
        r = self.emprestar(inicio=0, prazo=-1)
        self.assertIn("não pode ser anterior à data do empréstimo", self.texto(r))
        r = self.emprestar(inicio=3, prazo=10)
        self.assertIn("não pode ser futura", self.texto(r))
        self.assertEqual(self.contar("emprestimo"), 0)

    def test_renovacao_altera_a_data_prevista(self):
        self.criar_base()
        self.emprestar(inicio=-20, prazo=-5)
        r = self.post("/emprestimos/1/renovar", data_prevista=dia(7))
        self.assertIn("Data de devolução atualizada", self.texto(r))
        self.assertIn("No prazo", self.texto(self.cliente.get("/emprestimos/?situacao=no_prazo")))

    def test_livro_e_leitor_com_emprestimo_nao_podem_ser_excluidos(self):
        self.criar_base()
        self.emprestar()
        r = self.post("/livros/1/excluir")
        self.assertIn("existem empréstimos registrados para este livro", self.texto(r))
        r = self.post("/leitores/1/excluir")
        self.assertIn("existem empréstimos registrados para este leitor", self.texto(r))

        self.post("/emprestimos/1/excluir")
        self.assertEqual(self.contar("emprestimo"), 0)
        self.assertIn("Livro excluído", self.texto(self.post("/livros/1/excluir")))

    def test_quantidade_nao_fica_menor_que_emprestados(self):
        self.criar_base(quantidade="2")
        self.post("/leitores/novo", nome="Carlos Lima", email="carlos@example.com", telefone="")
        self.emprestar(leitor_id="1")
        self.emprestar(leitor_id="2")
        r = self.post("/livros/1/editar", titulo="Dom Casmurro", autor="Machado de Assis",
                      isbn="111", ano_publicacao="1899", quantidade="1", categoria_id="1")
        self.assertIn("A quantidade não pode ser menor que 2", self.texto(r))

    # ---------- geral ----------
    def test_painel_e_pagina_inexistente(self):
        self.criar_base()
        self.emprestar(inicio=-20, prazo=-5)
        pagina = self.texto(self.cliente.get("/"))
        self.assertIn("Empréstimos em atraso", pagina)
        self.assertIn("Dom Casmurro", pagina)
        self.assertEqual(self.cliente.get("/livros/999/editar").status_code, 404)


if __name__ == "__main__":
    unittest.main()
