"""Gera o arquivo docs/Documentacao.pdf.

Uso (na raiz do projeto):
    pip install reportlab
    python docs/gerar_documentacao.py

Altere os dados de identificação abaixo e gere o PDF novamente.
"""

from pathlib import Path

from reportlab.graphics.shapes import Circle, Drawing, Ellipse, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ----------------------------------------------------------------------------
# DADOS DE IDENTIFICAÇÃO — preencha antes de gerar a versão final
# ----------------------------------------------------------------------------
ALUNO = "Gregorio Alvares Ramires"
CURSO = "Engenharia de Software"
INSTITUICAO = "CENTRO UNIVERSITÁRIO FILADÉLFIA – UNIFIL"
DISCIPLINA = "Projeto de Desenvolvimento de Software II"
CIDADE = "Londrina"
ANO = "2026"
REPOSITORIO = "https://github.com/GregorioRamires/biblioteca-pds2"
DATA_ACESSO = "21 nov. 2026"
# ----------------------------------------------------------------------------

TITULO = "SISTEMA DE GERENCIAMENTO DE BIBLIOTECA"
PASTA = Path(__file__).parent
SAIDA = PASTA / "Documentacao.pdf"

AZUL = colors.HexColor("#1f4e5f")
AZUL_CLARO = colors.HexColor("#e8f0f3")
CINZA = colors.HexColor("#555555")

# Fonte Arial do Windows (aceita todos os acentos do português).
FONTES = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial", FONTES / "arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", FONTES / "arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", FONTES / "ariali.ttf"))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", FONTES / "arialbi.ttf"))
pdfmetrics.registerFontFamily(
    "Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic"
)

# Margens ABNT: superior e esquerda 3 cm; inferior e direita 2 cm.
LARGURA_PAGINA, ALTURA_PAGINA = A4
LARGURA_UTIL = LARGURA_PAGINA - 5 * cm

# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
CORPO = ParagraphStyle("Corpo", fontName="Arial", fontSize=12, leading=18, alignment=TA_JUSTIFY,
                       firstLineIndent=1.25 * cm, spaceAfter=6)
ITEM = ParagraphStyle("Item", parent=CORPO, firstLineIndent=0, leftIndent=1.25 * cm, bulletIndent=0.6 * cm,
                      spaceAfter=2)
TITULO1 = ParagraphStyle("Titulo1", fontName="Arial-Bold", fontSize=12, leading=18, spaceAfter=14)
TITULO1_CENTRO = ParagraphStyle("Titulo1Centro", parent=TITULO1, alignment=TA_CENTER)
TITULO_SEM_SUMARIO = ParagraphStyle("TituloSemSumario", parent=TITULO1, alignment=TA_CENTER)
TITULO2 = ParagraphStyle("Titulo2", fontName="Arial-Bold", fontSize=12, leading=18, spaceBefore=12, spaceAfter=6,
                         keepWithNext=1)
LEGENDA = ParagraphStyle("Legenda", fontName="Arial", fontSize=10, leading=13, alignment=TA_CENTER,
                         spaceBefore=8, spaceAfter=4, keepWithNext=1)
FONTE = ParagraphStyle("Fonte", parent=LEGENDA, spaceBefore=4, spaceAfter=12, keepWithNext=0)
CELULA = ParagraphStyle("Celula", fontName="Arial", fontSize=10, leading=13, alignment=TA_LEFT)
CELULA_CAB = ParagraphStyle("CelulaCab", parent=CELULA, fontName="Arial-Bold", textColor=colors.white)
REFERENCIA = ParagraphStyle("Referencia", fontName="Arial", fontSize=12, leading=15, alignment=TA_LEFT,
                            spaceAfter=14)
CODIGO = ParagraphStyle("Codigo", fontName="Courier", fontSize=9, leading=11.5, leftIndent=0.6 * cm,
                        spaceBefore=4, spaceAfter=10)
CAPA = ParagraphStyle("Capa", fontName="Arial", fontSize=12, leading=18, alignment=TA_CENTER)
CAPA_NEGRITO = ParagraphStyle("CapaNegrito", parent=CAPA, fontName="Arial-Bold")
CAPA_TITULO = ParagraphStyle("CapaTitulo", parent=CAPA, fontName="Arial-Bold", fontSize=16, leading=22)

NIVEIS_SUMARIO = {"Titulo1": 0, "Titulo1Centro": 0, "Titulo2": 1}


class Documento(BaseDocTemplate):
    """Documento A4 com sumário automático e numeração de páginas."""

    def __init__(self, arquivo):
        super().__init__(str(arquivo), pagesize=A4, leftMargin=3 * cm, rightMargin=2 * cm,
                         topMargin=3 * cm, bottomMargin=2 * cm,
                         title="Sistema de Gerenciamento de Biblioteca", author=ALUNO)
        quadro = Frame(3 * cm, 2 * cm, LARGURA_UTIL, ALTURA_PAGINA - 5 * cm,
                       leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="sem_numero", frames=[quadro]),
            PageTemplate(id="numerada", frames=[quadro], onPage=self._numero_da_pagina),
        ])
        self._marcador = 0

    @staticmethod
    def _numero_da_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont("Arial", 10)
        canvas.drawRightString(LARGURA_PAGINA - 2 * cm, ALTURA_PAGINA - 2 * cm, str(doc.page))
        canvas.restoreState()

    def beforeDocument(self):
        # O sumário exige mais de uma passada; os marcadores recomeçam a cada uma.
        self._marcador = 0

    def afterFlowable(self, flowable):
        """Registra os títulos no sumário à medida que são desenhados."""
        if isinstance(flowable, Paragraph) and flowable.style.name in NIVEIS_SUMARIO:
            self._marcador += 1
            chave = f"secao-{self._marcador}"
            self.canv.bookmarkPage(chave)
            self.notify("TOCEntry", (NIVEIS_SUMARIO[flowable.style.name], flowable.getPlainText(),
                                     self.page, chave))


# ----------------------------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------------------------
def p(texto):
    return Paragraph(texto, CORPO)


def itens(lista):
    return [Paragraph(texto, ITEM, bulletText="•") for texto in lista] + [Spacer(1, 6)]


def tabela(linhas, larguras):
    """Monta um quadro; a primeira linha é o cabeçalho."""
    dados = [[Paragraph(c, CELULA_CAB) for c in linhas[0]]]
    dados += [[Paragraph(c, CELULA) for c in linha] for linha in linhas[1:]]
    total = sum(larguras)
    t = Table(dados, colWidths=[LARGURA_UTIL * l / total for l in larguras], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f6f3")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def quadro(numero, titulo, linhas, larguras):
    # KeepTogether mantém título, quadro e fonte na mesma página.
    return [KeepTogether([Paragraph(f"Quadro {numero} – {titulo}", LEGENDA), tabela(linhas, larguras),
                          Paragraph(f"Fonte: elaborado pelo autor ({ANO}).", FONTE)])]


def figura(numero, titulo, conteudo):
    return KeepTogether([Paragraph(f"Figura {numero} – {titulo}", LEGENDA), conteudo,
                         Paragraph(f"Fonte: elaborado pelo autor ({ANO}).", FONTE)])


# ----------------------------------------------------------------------------
# Diagramas (desenhados em vetor)
# ----------------------------------------------------------------------------
def diagrama_casos_de_uso():
    largura, altura = LARGURA_UTIL, 345
    d = Drawing(largura, altura)
    casos = [
        "UC01 – Manter categorias",
        "UC02 – Manter livros",
        "UC03 – Manter leitores",
        "UC04 – Registrar empréstimo",
        "UC05 – Registrar devolução",
        "UC06 – Renovar empréstimo",
        "UC07 – Consultar painel e atrasos",
    ]
    # Fronteira do sistema
    d.add(Rect(150, 8, largura - 158, altura - 16, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    centro_x = 150 + (largura - 158) / 2
    d.add(String(centro_x, altura - 28, "Sistema de Gerenciamento de Biblioteca",
                 textAnchor="middle", fontName="Arial-Bold", fontSize=10))

    # Ator
    ax, ay = 55, altura / 2
    d.add(Circle(ax, ay + 30, 9, fillColor=colors.white, strokeColor=colors.black))
    d.add(Line(ax, ay + 21, ax, ay - 6))
    d.add(Line(ax - 17, ay + 11, ax + 17, ay + 11))
    d.add(Line(ax, ay - 6, ax - 13, ay - 28))
    d.add(Line(ax, ay - 6, ax + 13, ay - 28))
    d.add(String(ax, ay - 44, "Bibliotecário", textAnchor="middle", fontName="Arial", fontSize=10))

    topo, base = altura - 68, 40
    passo = (topo - base) / (len(casos) - 1)
    raio_x, raio_y = 112, 15
    for i, nome in enumerate(casos):
        y = topo - i * passo
        d.add(Line(ax + 22, ay + 4, centro_x - raio_x, y, strokeColor=colors.black, strokeWidth=0.7))
        d.add(Ellipse(centro_x, y, raio_x, raio_y, fillColor=AZUL_CLARO, strokeColor=AZUL, strokeWidth=1))
        d.add(String(centro_x, y - 3.5, nome, textAnchor="middle", fontName="Arial", fontSize=9.5))
    return d


def _entidade(d, x, topo, largura, nome, atributos):
    alt_cab, alt_linha = 20, 14
    altura = alt_cab + len(atributos) * alt_linha + 6
    d.add(Rect(x, topo - altura, largura, altura, fillColor=colors.white, strokeColor=colors.black))
    d.add(Rect(x, topo - alt_cab, largura, alt_cab, fillColor=AZUL, strokeColor=colors.black))
    d.add(String(x + largura / 2, topo - 14, nome, textAnchor="middle", fontName="Arial-Bold",
                 fontSize=10, fillColor=colors.white))
    for i, (marca, atributo, tipo) in enumerate(atributos):
        y = topo - alt_cab - 13 - i * alt_linha
        d.add(String(x + 6, y, marca, fontName="Arial-Bold", fontSize=8, fillColor=AZUL))
        d.add(String(x + 28, y, atributo, fontName="Arial", fontSize=9))
        d.add(String(x + largura - 6, y, tipo, textAnchor="end", fontName="Arial", fontSize=8, fillColor=CINZA))
    return altura


def diagrama_er():
    largura, altura = LARGURA_UTIL, 305
    d = Drawing(largura, altura)
    caixa = 185
    x_esq, x_dir = 4, largura - caixa - 4
    topo = altura - 5

    alt_categoria = _entidade(d, x_esq, topo, caixa, "CATEGORIA", [
        ("PK", "id", "INTEGER"), ("", "nome", "TEXT"), ("", "descricao", "TEXT")])
    alt_livro = _entidade(d, x_dir, topo, caixa, "LIVRO", [
        ("PK", "id", "INTEGER"), ("", "titulo", "TEXT"), ("", "autor", "TEXT"), ("", "isbn", "TEXT"),
        ("", "ano_publicacao", "INTEGER"), ("", "quantidade", "INTEGER"), ("FK", "categoria_id", "INTEGER")])
    topo_baixo = topo - alt_livro - 56
    _entidade(d, x_dir, topo_baixo, caixa, "EMPRESTIMO", [
        ("PK", "id", "INTEGER"), ("FK", "livro_id", "INTEGER"), ("FK", "leitor_id", "INTEGER"),
        ("", "data_emprestimo", "TEXT (data)"), ("", "data_prevista", "TEXT (data)"),
        ("", "data_devolucao", "TEXT (data)")])
    _entidade(d, x_esq, topo_baixo, caixa, "LEITOR", [
        ("PK", "id", "INTEGER"), ("", "nome", "TEXT"), ("", "email", "TEXT"), ("", "telefone", "TEXT"),
        ("", "data_cadastro", "TEXT (data)")])

    def rotulo(x, y, texto, ancora="start", negrito=True):
        d.add(String(x, y, texto, textAnchor=ancora, fontSize=9 if negrito else 8,
                     fontName="Arial-Bold" if negrito else "Arial-Italic"))

    x1, x2 = x_esq + caixa, x_dir
    meio_x = (x1 + x2) / 2

    # CATEGORIA 1 — N LIVRO
    y = topo - alt_categoria / 2
    d.add(Line(x1, y, x2, y))
    rotulo(x1 + 5, y + 4, "1")
    rotulo(x2 - 5, y + 4, "N", "end")
    rotulo(meio_x, y - 11, "classifica", "middle", negrito=False)

    # LIVRO 1 — N EMPRESTIMO
    x = x_dir + caixa / 2
    y_cima, y_baixo = topo - alt_livro, topo_baixo
    d.add(Line(x, y_cima, x, y_baixo))
    rotulo(x + 5, y_cima - 11, "1")
    rotulo(x + 5, y_baixo + 4, "N")
    rotulo(x - 6, (y_cima + y_baixo) / 2 - 3, "é emprestado em", "end", negrito=False)

    # LEITOR 1 — N EMPRESTIMO
    y = topo_baixo - 45
    d.add(Line(x1, y, x2, y))
    rotulo(x1 + 5, y + 4, "1")
    rotulo(x2 - 5, y + 4, "N", "end")
    rotulo(meio_x, y - 11, "realiza", "middle", negrito=False)
    return d


# ----------------------------------------------------------------------------
# Conteúdo
# ----------------------------------------------------------------------------
def capa():
    return [
        Paragraph(INSTITUICAO, CAPA_NEGRITO),
        Paragraph(CURSO.upper(), CAPA),
        Spacer(1, 4.5 * cm),
        Paragraph(ALUNO.upper(), CAPA),
        Spacer(1, 4.5 * cm),
        Paragraph(TITULO, CAPA_TITULO),
        Spacer(1, 0.4 * cm),
        Paragraph(f"Documentação do projeto da disciplina<br/>{DISCIPLINA}", CAPA),
        Spacer(1, 8.6 * cm),
        Paragraph(CIDADE, CAPA),
        Paragraph(ANO, CAPA),
        PageBreak(),
    ]


def sumario():
    indice = TableOfContents(dotsMinLevel=0)
    indice.levelStyles = [
        ParagraphStyle("Sumario1", fontName="Arial-Bold", fontSize=12, leading=20),
        ParagraphStyle("Sumario2", fontName="Arial", fontSize=12, leading=20, leftIndent=0.6 * cm),
    ]
    return [Paragraph("SUMÁRIO", TITULO_SEM_SUMARIO), indice, NextPageTemplate("numerada"), PageBreak()]


def introducao():
    return [
        Paragraph("1 INTRODUÇÃO", TITULO1),
        p("Bibliotecas pequenas, como as de escolas, igrejas e associações de bairro, normalmente "
          "controlam seus empréstimos em cadernos ou planilhas. Esse controle manual gera problemas: "
          "não se sabe com quem está determinado livro, um mesmo exemplar é prometido para duas "
          "pessoas e os atrasos passam despercebidos."),
        p("Este trabalho apresenta o <b>Sistema de Gerenciamento de Biblioteca</b>, uma aplicação web "
          "desenvolvida para a disciplina de Projeto de Desenvolvimento de Software II. O sistema "
          "permite ao bibliotecário cadastrar categorias, livros e leitores, registrar empréstimos e "
          "devoluções e acompanhar, em um painel, os empréstimos em atraso. Ele se comunica com um "
          "banco de dados relacional e implementa as quatro operações de CRUD (criar, consultar, "
          "atualizar e excluir) para todas as entidades."),

        Paragraph("1.1 Objetivos", TITULO2),
        p("O objetivo geral é desenvolver um sistema web que substitua o controle manual de "
          "empréstimos de uma biblioteca de pequeno porte. Os objetivos específicos são:"),
        *itens([
            "levantar os requisitos funcionais e não funcionais do sistema;",
            "modelar o sistema com diagrama de casos de uso e diagrama entidade-relacionamento;",
            "implementar o sistema conforme a documentação e publicá-lo no GitHub.",
        ]),

        Paragraph("1.2 Stack utilizada", TITULO2),
        p("O sistema foi escrito em <b>Python 3.12</b> com o microframework web <b>Flask</b>, que "
          "recebe as requisições, define as rotas e devolve as páginas (PALLETS, 2026). Os dados são "
          "gravados em um banco relacional <b>SQLite</b> (SQLITE, 2026), acessado com comandos SQL "
          "pelo módulo sqlite3 da biblioteca padrão do Python (PYTHON SOFTWARE FOUNDATION, 2026). As "
          "telas são páginas <b>HTML e CSS</b> geradas por <i>templates</i> Jinja2. O projeto possui "
          "testes automatizados com a biblioteca unittest e é versionado com <b>Git</b>."),
        p(f"O projeto foi desenvolvido individualmente por {ALUNO}. O código-fonte está disponível "
          f"em: {REPOSITORIO}."),
        PageBreak(),
    ]


def desenvolvimento():
    return [
        Paragraph("2 DESENVOLVIMENTO", TITULO1),
        p("Este capítulo apresenta os requisitos do sistema, o diagrama de casos de uso e o "
          "diagrama entidade-relacionamento."),

        Paragraph("2.1 Requisitos funcionais", TITULO2),
        p("Os requisitos funcionais descrevem o que o sistema deve fazer (SOMMERVILLE, 2018). "
          "O Quadro 1 lista os requisitos funcionais, todos implementados."),
        *quadro(1, "Requisitos funcionais", [
            ["Código", "Descrição", "Prioridade"],
            ["RF01", "Cadastrar, listar, editar e excluir categorias de livros.", "Essencial"],
            ["RF02", "Cadastrar, listar, editar e excluir livros, com título, autor, ISBN, ano de "
                     "publicação, quantidade de exemplares e categoria.", "Essencial"],
            ["RF03", "Buscar livros por título ou autor e filtrá-los por categoria.", "Importante"],
            ["RF04", "Cadastrar, listar, buscar, editar e excluir leitores, com nome, e-mail e "
                     "telefone.", "Essencial"],
            ["RF05", "Registrar o empréstimo de um livro a um leitor, com a data do empréstimo e a "
                     "data prevista de devolução.", "Essencial"],
            ["RF06", "Registrar a devolução de um livro emprestado.", "Essencial"],
            ["RF07", "Renovar um empréstimo, alterando a data prevista de devolução.", "Importante"],
            ["RF08", "Listar os empréstimos, filtrá-los pela situação (no prazo, atrasado ou "
                     "devolvido) e excluir um registro lançado por engano.", "Essencial"],
            ["RF09", "Exibir, para cada livro, quantos exemplares estão disponíveis.", "Essencial"],
            ["RF10", "Impedir o empréstimo de livro sem exemplar disponível e o empréstimo a leitor "
                     "com devolução em atraso.", "Essencial"],
            ["RF11", "Impedir a exclusão de categoria que possua livros e de livro ou leitor que "
                     "possua empréstimos registrados.", "Essencial"],
            ["RF12", "Exibir um painel com os totais do acervo e os empréstimos em atraso.", "Desejável"],
        ], [1.6, 9.6, 2.2]),

        Paragraph("2.2 Requisitos não funcionais", TITULO2),
        p("Os requisitos não funcionais definem restrições e qualidades do sistema. Eles estão "
          "listados no Quadro 2."),
        *quadro(2, "Requisitos não funcionais", [
            ["Código", "Categoria", "Descrição"],
            ["RNF01", "Persistência", "Os dados devem ser gravados em banco de dados relacional (SQLite), "
                                      "com integridade referencial por chaves estrangeiras."],
            ["RNF02", "Usabilidade", "A interface deve ser em português, exibir mensagens claras de "
                                     "sucesso e de erro e pedir confirmação antes de excluir."],
            ["RNF03", "Portabilidade", "O sistema deve funcionar nos navegadores atuais e adaptar o "
                                       "layout a telas de computador e de celular."],
            ["RNF04", "Segurança", "As consultas ao banco devem ser parametrizadas, para impedir "
                                   "injeção de SQL."],
            ["RNF05", "Confiabilidade", "Os dados recebidos devem ser validados no servidor e por "
                                        "restrições do banco (NOT NULL, UNIQUE e CHECK)."],
            ["RNF06", "Manutenibilidade", "O código deve ser organizado em módulos, um por entidade, e "
                                          "possuir testes automatizados."],
            ["RNF07", "Versionamento", "O código-fonte deve ser versionado com Git e publicado no GitHub."],
        ], [1.7, 3.1, 8.6]),

        Paragraph("2.3 Diagrama de casos de uso", TITULO2),
        p("O diagrama de casos de uso representa as funcionalidades do sistema do ponto de vista de "
          "quem o utiliza (GUEDES, 2018). O sistema possui um único ator, o bibliotecário, e sete "
          "casos de uso, apresentados na Figura 1 e descritos no Quadro 3."),
        *quadro(3, "Descrição dos casos de uso", [
            ["Caso de uso", "Descrição", "Requisitos"],
            ["UC01 – Manter categorias", "Cadastrar, consultar, alterar e excluir as categorias dos "
                                         "livros.", "RF01, RF11"],
            ["UC02 – Manter livros", "Cadastrar, consultar, buscar, alterar e excluir os livros do "
                                     "acervo.", "RF02, RF03, RF09, RF11"],
            ["UC03 – Manter leitores", "Cadastrar, consultar, buscar, alterar e excluir os leitores.",
             "RF04, RF11"],
            ["UC04 – Registrar empréstimo", "Registrar a saída de um livro para um leitor, se houver "
                                            "exemplar disponível e o leitor não estiver em atraso.",
             "RF05, RF10"],
            ["UC05 – Registrar devolução", "Registrar o retorno de um livro, que volta a ficar "
                                           "disponível.", "RF06"],
            ["UC06 – Renovar empréstimo", "Alterar a data prevista de devolução de um empréstimo em "
                                          "aberto.", "RF07"],
            ["UC07 – Consultar painel e atrasos", "Consultar os totais do acervo e os empréstimos por "
                                                  "situação, e excluir lançamentos incorretos.",
             "RF08, RF12"],
        ], [4.2, 6.6, 2.6]),
        figura(1, "Diagrama de casos de uso", diagrama_casos_de_uso()),

        Paragraph("2.4 Diagrama entidade-relacionamento", TITULO2),
        p("O banco de dados possui quatro entidades: categoria, livro, leitor e empréstimo. A "
          "Figura 2 apresenta o diagrama entidade-relacionamento (DER), com os atributos, as chaves "
          "primárias (PK), as chaves estrangeiras (FK) e a cardinalidade dos relacionamentos "
          "(ELMASRI; NAVATHE, 2018)."),
        figura(2, "Diagrama entidade-relacionamento", diagrama_er()),
        p("Os relacionamentos do modelo são os seguintes:"),
        *itens([
            "<b>Categoria classifica livro (1:N):</b> uma categoria pode ter vários livros, e cada "
            "livro pertence a uma única categoria.",
            "<b>Livro é emprestado em empréstimo (1:N):</b> um livro pode aparecer em vários "
            "empréstimos, e cada empréstimo se refere a um único livro.",
            "<b>Leitor realiza empréstimo (1:N):</b> um leitor pode realizar vários empréstimos, e "
            "cada empréstimo pertence a um único leitor.",
        ]),
        p("Entre livro e leitor existe, portanto, um relacionamento de muitos para muitos, resolvido "
          "pela entidade empréstimo. A situação do empréstimo (no prazo, atrasado ou devolvido) e a "
          "quantidade de exemplares disponíveis não são gravadas: são calculadas a partir das datas "
          "e dos empréstimos em aberto, o que evita informação redundante. As chaves estrangeiras "
          "usam a opção ON DELETE RESTRICT, que impede no próprio banco a exclusão de um registro "
          "referenciado por outro, como um livro que possui empréstimos."),
        PageBreak(),
    ]


def conclusao():
    return [
        Paragraph("3 CONCLUSÃO", TITULO1),
        p("O objetivo do projeto foi atingido: o sistema desenvolvido realiza as operações de CRUD "
          "sobre categorias, livros, leitores e empréstimos, comunica-se com um banco de dados "
          "relacional e atende aos requisitos funcionais e não funcionais documentados."),
        p("O principal aprendizado foi perceber o valor de documentar antes de programar. Com os "
          "requisitos, os casos de uso e o DER definidos, a implementação tornou-se uma tradução "
          "direta: cada entidade do diagrama virou uma tabela e um módulo do sistema, e cada caso de "
          "uso virou um conjunto de telas e rotas."),
        p("Na parte de banco de dados, aprendi na prática a importância das chaves estrangeiras e "
          "das restrições: deixar o próprio banco recusar um dado inconsistente é mais seguro do que "
          "depender apenas das validações da aplicação. No desenvolvimento web, aprendi como "
          "funciona o ciclo de requisição e resposta, a diferença entre os métodos GET e POST e a "
          "organização de um projeto Flask em módulos."),
        p("Como trabalhos futuros, o sistema pode receber autenticação de usuários, cálculo de multa "
          "por atraso, reserva de livros indisponíveis e relatórios dos livros mais emprestados."),
        PageBreak(),
    ]


def referencias():
    lista = [
        "ELMASRI, Ramez; NAVATHE, Shamkant B. <b>Sistemas de banco de dados</b>. 7. ed. São Paulo: "
        "Pearson Education do Brasil, 2018.",
        "GUEDES, Gilleanes T. A. <b>UML 2</b>: uma abordagem prática. 3. ed. São Paulo: Novatec, 2018.",
        f"PALLETS. <b>Flask documentation</b>. 2026. Disponível em: https://flask.palletsprojects.com/. "
        f"Acesso em: {DATA_ACESSO}.",
        "PYTHON SOFTWARE FOUNDATION. <b>sqlite3</b>: DB-API 2.0 interface for SQLite databases. 2026. "
        f"Disponível em: https://docs.python.org/3/library/sqlite3.html. Acesso em: {DATA_ACESSO}.",
        "SOMMERVILLE, Ian. <b>Engenharia de software</b>. 10. ed. São Paulo: Pearson Education do "
        "Brasil, 2018.",
        f"SQLITE. <b>SQLite documentation</b>. 2026. Disponível em: https://www.sqlite.org/docs.html. "
        f"Acesso em: {DATA_ACESSO}.",
    ]
    return [Paragraph("REFERÊNCIAS", TITULO1_CENTRO)] + [Paragraph(r, REFERENCIA) for r in lista]


def gerar():
    historia = capa() + sumario() + introducao() + desenvolvimento() + conclusao() + referencias()
    Documento(SAIDA).multiBuild(historia)
    print(f"PDF gerado em: {SAIDA}")


if __name__ == "__main__":
    gerar()
