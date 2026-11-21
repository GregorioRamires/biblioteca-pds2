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
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle,
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
IMAGENS = PASTA / "img"

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


def captura(nome, largura_px, altura_px):
    largura = 14 * cm
    img = Image(str(IMAGENS / nome), width=largura, height=largura * altura_px / largura_px)
    borda = Table([[img]], colWidths=[largura])
    borda.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return borda


# ----------------------------------------------------------------------------
# Diagramas (desenhados em vetor)
# ----------------------------------------------------------------------------
def diagrama_casos_de_uso():
    largura, altura = LARGURA_UTIL, 400
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
    raio_x, raio_y = 112, 18
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
        p("Bibliotecas pequenas, como as de escolas, igrejas, associações de bairro e empresas, "
          "normalmente controlam seus empréstimos em cadernos ou planilhas. Esse controle manual "
          "funciona enquanto o acervo é pequeno, mas rapidamente gera problemas: não se sabe com "
          "quem está determinado livro, um mesmo exemplar é prometido para duas pessoas, os atrasos "
          "passam despercebidos e os dados dos leitores ficam espalhados e desatualizados."),
        p("Este trabalho apresenta o <b>Sistema de Gerenciamento de Biblioteca</b>, uma aplicação web "
          "desenvolvida para a disciplina de Projeto de Desenvolvimento de Software II. O sistema "
          "permite ao bibliotecário cadastrar categorias, livros e leitores, registrar empréstimos e "
          "devoluções e acompanhar, em um painel, a situação do acervo e os empréstimos em atraso."),
        p("O sistema se comunica com um banco de dados relacional e implementa as quatro operações de "
          "CRUD (criar, consultar, atualizar e excluir) para todas as entidades. Além do CRUD, foram "
          "implementadas regras de negócio próprias do domínio, como o controle de exemplares "
          "disponíveis e o bloqueio de novos empréstimos para leitores com devolução em atraso."),

        Paragraph("1.1 Objetivos", TITULO2),
        p("O objetivo geral do projeto é desenvolver um sistema web que substitua o controle manual "
          "de empréstimos de uma biblioteca de pequeno porte. Os objetivos específicos são:"),
        *itens([
            "levantar e documentar os requisitos funcionais e não funcionais do sistema;",
            "modelar o sistema por meio de diagrama de casos de uso e de diagrama "
            "entidade-relacionamento (DER);",
            "implementar o sistema de acordo com a documentação, com persistência em banco de dados "
            "relacional;",
            "garantir a integridade dos dados por meio de validações e de restrições no banco;",
            "versionar o código-fonte com Git e publicá-lo em um repositório no GitHub.",
        ]),

        Paragraph("1.2 Stack utilizada", TITULO2),
        p("As tecnologias foram escolhidas por serem gratuitas, bem documentadas e simples de "
          "instalar, o que permite que qualquer pessoa execute o projeto apenas com o Python "
          "instalado. O Quadro 1 apresenta cada tecnologia e a sua função no projeto."),
        *quadro(1, "Tecnologias utilizadas no projeto", [
            ["Tecnologia", "Função no projeto"],
            ["Python 3.12", "Linguagem de programação de toda a aplicação."],
            ["Flask 3", "Microframework web: recebe as requisições HTTP, define as rotas e devolve as páginas."],
            ["SQLite 3", "Banco de dados relacional, gravado em um único arquivo e acessado pelo módulo "
                         "<i>sqlite3</i> da biblioteca padrão do Python, com comandos SQL escritos manualmente."],
            ["Jinja2", "Motor de <i>templates</i> que gera as páginas HTML a partir dos dados do banco."],
            ["HTML5 e CSS3", "Estrutura e aparência das telas, com layout responsivo e sem dependências externas."],
            ["unittest", "Biblioteca padrão do Python usada para os testes automatizados."],
            ["Git e GitHub", "Controle de versão e hospedagem do repositório do projeto."],
        ], [3, 10]),

        Paragraph("1.3 Autoria e repositório", TITULO2),
        p(f"O projeto foi desenvolvido individualmente por {ALUNO}. O código-fonte está disponível "
          f"no repositório do GitHub: {REPOSITORIO}."),
        PageBreak(),
    ]


def desenvolvimento():
    partes = [
        Paragraph("2 DESENVOLVIMENTO", TITULO1),
        p("Este capítulo apresenta os requisitos levantados, as regras de negócio, os diagramas "
          "de casos de uso e de entidade-relacionamento e, por fim, a implementação do sistema."),

        Paragraph("2.1 Requisitos funcionais", TITULO2),
        p("Os requisitos funcionais descrevem o que o sistema deve fazer (SOMMERVILLE, 2018). "
          "O Quadro 2 lista os requisitos funcionais do sistema, todos implementados."),
        *quadro(2, "Requisitos funcionais", [
            ["Código", "Descrição", "Prioridade"],
            ["RF01", "O sistema deve permitir cadastrar, listar, editar e excluir categorias de livros.", "Essencial"],
            ["RF02", "O sistema deve permitir cadastrar, listar, editar e excluir livros, com título, autor, "
                     "ISBN, ano de publicação, quantidade de exemplares e categoria.", "Essencial"],
            ["RF03", "O sistema deve permitir buscar livros por título ou autor e filtrá-los por categoria.", "Importante"],
            ["RF04", "O sistema deve permitir cadastrar, listar, editar e excluir leitores, com nome, e-mail "
                     "e telefone.", "Essencial"],
            ["RF05", "O sistema deve permitir buscar leitores por nome ou e-mail.", "Importante"],
            ["RF06", "O sistema deve permitir registrar o empréstimo de um livro a um leitor, com a data do "
                     "empréstimo e a data prevista de devolução.", "Essencial"],
            ["RF07", "O sistema deve permitir registrar a devolução de um livro emprestado.", "Essencial"],
            ["RF08", "O sistema deve permitir renovar um empréstimo, alterando a data prevista de devolução.", "Importante"],
            ["RF09", "O sistema deve listar os empréstimos e permitir filtrá-los pela situação: no prazo, "
                     "atrasado ou devolvido.", "Essencial"],
            ["RF10", "O sistema deve permitir excluir um registro de empréstimo lançado por engano.", "Importante"],
            ["RF11", "O sistema deve exibir, para cada livro, quantos exemplares estão disponíveis.", "Essencial"],
            ["RF12", "O sistema deve exibir um painel com os totais do acervo e a lista de empréstimos em atraso.", "Desejável"],
        ], [1.6, 9.6, 2.2]),

        Paragraph("2.2 Requisitos não funcionais", TITULO2),
        p("Os requisitos não funcionais definem restrições e qualidades do sistema, como segurança, "
          "usabilidade e manutenibilidade. Eles estão listados no Quadro 3."),
        *quadro(3, "Requisitos não funcionais", [
            ["Código", "Categoria", "Descrição"],
            ["RNF01", "Persistência", "Os dados devem ser gravados em banco de dados relacional (SQLite), com "
                                      "integridade referencial garantida por chaves estrangeiras."],
            ["RNF02", "Usabilidade", "A interface deve ser em português, exibir mensagens claras de sucesso e de "
                                     "erro e pedir confirmação antes de qualquer exclusão."],
            ["RNF03", "Portabilidade", "O sistema deve funcionar nos navegadores atuais (Chrome, Edge e Firefox) "
                                       "e adaptar o layout a telas de computador e de celular."],
            ["RNF04", "Segurança", "Todas as consultas ao banco devem ser parametrizadas, para impedir injeção de "
                                   "SQL, e todo dado exibido nas páginas deve ser escapado, para impedir a "
                                   "injeção de scripts."],
            ["RNF05", "Confiabilidade", "Todos os dados recebidos devem ser validados no servidor, e as regras "
                                        "essenciais devem existir também no banco (NOT NULL, UNIQUE e CHECK)."],
            ["RNF06", "Manutenibilidade", "O código deve ser organizado em módulos, um por entidade, e possuir "
                                          "testes automatizados das principais funcionalidades."],
            ["RNF07", "Instalação", "O sistema deve depender apenas do Python e do Flask, e o banco de dados deve "
                                    "ser criado automaticamente na primeira execução."],
            ["RNF08", "Versionamento", "O código-fonte deve ser versionado com Git e publicado no GitHub."],
        ], [1.7, 3.1, 8.6]),

        Paragraph("2.3 Regras de negócio", TITULO2),
        p("Além dos requisitos, foram definidas as regras de negócio do Quadro 4. Elas são verificadas "
          "pelo sistema sempre que um dado é gravado."),
        *quadro(4, "Regras de negócio", [
            ["Código", "Regra"],
            ["RN01", "Um livro só pode ser emprestado se houver pelo menos um exemplar disponível "
                     "(quantidade cadastrada menos exemplares emprestados)."],
            ["RN02", "Um leitor com empréstimo em atraso não pode realizar novo empréstimo."],
            ["RN03", "Cada leitor pode ter, no máximo, três empréstimos em aberto ao mesmo tempo."],
            ["RN04", "O prazo padrão de devolução é de 14 dias, podendo ser alterado no momento do empréstimo "
                     "ou na renovação."],
            ["RN05", "A data do empréstimo não pode ser futura, e a data prevista de devolução não pode ser "
                     "anterior à data do empréstimo."],
            ["RN06", "Não é permitido excluir uma categoria que possua livros, nem um livro ou um leitor que "
                     "possua empréstimos registrados."],
            ["RN07", "A quantidade de exemplares de um livro não pode ser reduzida para um valor menor que o "
                     "número de exemplares emprestados no momento."],
            ["RN08", "O nome da categoria, o ISBN do livro e o e-mail do leitor não podem se repetir."],
        ], [1.6, 11.8]),

        Paragraph("2.4 Diagrama de casos de uso", TITULO2),
        p("O diagrama de casos de uso representa as funcionalidades do sistema do ponto de vista de "
          "quem o utiliza (GUEDES, 2018). O sistema possui um único ator, o bibliotecário, que realiza "
          "os sete casos de uso apresentados na Figura 1."),
        figura(1, "Diagrama de casos de uso", diagrama_casos_de_uso()),
        p("O Quadro 5 descreve resumidamente cada caso de uso e indica os requisitos funcionais "
          "atendidos por ele."),
        *quadro(5, "Descrição dos casos de uso", [
            ["Caso de uso", "Descrição", "Requisitos"],
            ["UC01 – Manter categorias", "O bibliotecário cadastra, consulta, altera e exclui as categorias "
                                         "usadas para classificar os livros.", "RF01"],
            ["UC02 – Manter livros", "O bibliotecário cadastra, consulta, busca, altera e exclui os livros "
                                     "do acervo.", "RF02, RF03, RF11"],
            ["UC03 – Manter leitores", "O bibliotecário cadastra, consulta, busca, altera e exclui os leitores.",
             "RF04, RF05"],
            ["UC04 – Registrar empréstimo", "O bibliotecário registra a saída de um livro para um leitor.",
             "RF06"],
            ["UC05 – Registrar devolução", "O bibliotecário registra o retorno de um livro emprestado, que "
                                           "volta a ficar disponível.", "RF07"],
            ["UC06 – Renovar empréstimo", "O bibliotecário altera a data prevista de devolução de um "
                                          "empréstimo em aberto.", "RF08"],
            ["UC07 – Consultar painel e atrasos", "O bibliotecário consulta os totais do acervo e os "
                                                  "empréstimos por situação, e exclui lançamentos incorretos.",
             "RF09, RF10, RF12"],
        ], [4.2, 6.8, 2.4]),
        p("O caso de uso mais importante do sistema, por concentrar a maior parte das regras de "
          "negócio, é o UC04. Sua especificação completa está no Quadro 6."),
        *quadro(6, "Especificação do caso de uso UC04 – Registrar empréstimo", [
            ["Item", "Descrição"],
            ["Ator", "Bibliotecário."],
            ["Pré-condições", "Existir ao menos um leitor cadastrado e um livro com exemplar disponível."],
            ["Fluxo principal",
             "1. O bibliotecário acessa a tela de empréstimos e escolhe “Novo empréstimo”.<br/>"
             "2. O sistema exibe os livros com exemplar disponível e os leitores cadastrados, sugerindo a "
             "data atual e a devolução em 14 dias.<br/>"
             "3. O bibliotecário seleciona o livro e o leitor e, se necessário, ajusta as datas.<br/>"
             "4. O sistema valida os dados e as regras de negócio.<br/>"
             "5. O sistema grava o empréstimo e exibe a mensagem de sucesso."],
            ["Fluxos alternativos",
             "4a. Não há exemplar disponível (RN01): o sistema informa o erro e não grava.<br/>"
             "4b. O leitor possui empréstimo em atraso (RN02): o sistema informa o erro e não grava.<br/>"
             "4c. O leitor atingiu o limite de três empréstimos (RN03): o sistema informa o erro e não grava.<br/>"
             "4d. As datas são inválidas (RN05): o sistema informa o erro e mantém os dados preenchidos."],
            ["Pós-condições", "O empréstimo fica registrado com a situação “no prazo”, e a quantidade de "
                              "exemplares disponíveis do livro diminui em uma unidade."],
        ], [3.2, 10.2]),

        Paragraph("2.5 Diagrama entidade-relacionamento", TITULO2),
        p("O banco de dados foi modelado com quatro entidades: categoria, livro, leitor e empréstimo. "
          "A Figura 2 apresenta o diagrama entidade-relacionamento (DER), com os atributos de cada "
          "entidade, as chaves primárias (PK), as chaves estrangeiras (FK) e a cardinalidade dos "
          "relacionamentos (ELMASRI; NAVATHE, 2018)."),
        figura(2, "Diagrama entidade-relacionamento", diagrama_er()),
        p("Os relacionamentos do modelo são os seguintes:"),
        *itens([
            "<b>Categoria classifica livro (1:N):</b> uma categoria pode ter vários livros, e cada livro "
            "pertence a exatamente uma categoria.",
            "<b>Livro é emprestado em empréstimo (1:N):</b> um livro pode aparecer em vários empréstimos "
            "ao longo do tempo, e cada empréstimo se refere a um único livro.",
            "<b>Leitor realiza empréstimo (1:N):</b> um leitor pode realizar vários empréstimos, e cada "
            "empréstimo pertence a um único leitor.",
        ]),
        p("Entre livro e leitor existe, portanto, um relacionamento de muitos para muitos, resolvido "
          "pela entidade empréstimo, que guarda também as datas de cada operação. A situação do "
          "empréstimo (no prazo, atrasado ou devolvido) não é armazenada: ela é calculada a partir "
          "das datas no momento da consulta, o que evita guardar uma informação redundante que "
          "poderia ficar desatualizada. Pelo mesmo motivo, a quantidade de exemplares disponíveis é "
          "calculada, e não gravada."),
        p("Os Quadros 7 a 10 apresentam o dicionário de dados de cada tabela."),
        *quadro(7, "Dicionário de dados da tabela categoria", [
            ["Campo", "Tipo", "Restrições", "Descrição"],
            ["id", "INTEGER", "PK, autoincremento", "Identificador da categoria."],
            ["nome", "TEXT", "NOT NULL, UNIQUE", "Nome da categoria."],
            ["descricao", "TEXT", "—", "Descrição opcional."],
        ], [3, 2, 3.6, 4.8]),
        *quadro(8, "Dicionário de dados da tabela livro", [
            ["Campo", "Tipo", "Restrições", "Descrição"],
            ["id", "INTEGER", "PK, autoincremento", "Identificador do livro."],
            ["titulo", "TEXT", "NOT NULL", "Título do livro."],
            ["autor", "TEXT", "NOT NULL", "Autor ou autores."],
            ["isbn", "TEXT", "UNIQUE", "Código ISBN (opcional)."],
            ["ano_publicacao", "INTEGER", "—", "Ano de publicação (opcional)."],
            ["quantidade", "INTEGER", "NOT NULL, CHECK (≥ 0)", "Total de exemplares do acervo."],
            ["categoria_id", "INTEGER", "NOT NULL, FK → categoria", "Categoria do livro."],
        ], [3, 2, 3.6, 4.8]),
        *quadro(9, "Dicionário de dados da tabela leitor", [
            ["Campo", "Tipo", "Restrições", "Descrição"],
            ["id", "INTEGER", "PK, autoincremento", "Identificador do leitor."],
            ["nome", "TEXT", "NOT NULL", "Nome completo."],
            ["email", "TEXT", "NOT NULL, UNIQUE", "E-mail de contato."],
            ["telefone", "TEXT", "—", "Telefone com DDD (opcional)."],
            ["data_cadastro", "TEXT", "NOT NULL", "Data do cadastro, no formato AAAA-MM-DD."],
        ], [3, 2, 3.6, 4.8]),
        *quadro(10, "Dicionário de dados da tabela emprestimo", [
            ["Campo", "Tipo", "Restrições", "Descrição"],
            ["id", "INTEGER", "PK, autoincremento", "Identificador do empréstimo."],
            ["livro_id", "INTEGER", "NOT NULL, FK → livro", "Livro emprestado."],
            ["leitor_id", "INTEGER", "NOT NULL, FK → leitor", "Leitor que pegou o livro."],
            ["data_emprestimo", "TEXT", "NOT NULL", "Data da retirada."],
            ["data_prevista", "TEXT", "NOT NULL, CHECK (≥ data_emprestimo)", "Data limite para devolução."],
            ["data_devolucao", "TEXT", "—", "Data da devolução; vazia enquanto o livro não é devolvido."],
        ], [3, 2, 3.6, 4.8]),
        p("O SQLite não possui um tipo específico para datas; por isso elas são gravadas como texto no "
          "padrão ISO 8601 (AAAA-MM-DD), que mantém a ordem cronológica quando comparado (SQLITE, 2026). "
          "Todas as chaves estrangeiras usam a opção ON DELETE RESTRICT, que impede a exclusão de um "
          "registro referenciado por outro e implementa a regra RN06 diretamente no banco."),

        Paragraph("2.6 Implementação", TITULO2),
        p("O sistema foi implementado como uma aplicação web em camadas simples. O navegador envia "
          "uma requisição HTTP, o Flask a encaminha para a função responsável pela rota, essa função "
          "valida os dados, executa os comandos SQL no SQLite e devolve uma página HTML gerada por "
          "um <i>template</i> Jinja2 (PALLETS, 2026). O código foi dividido em módulos, um para cada "
          "entidade, registrados no Flask como <i>blueprints</i>. A organização das pastas é a seguinte:"),
        KeepTogether([Preformatted(
            "biblioteca-pds2/\n"
            "  run.py             inicia o servidor\n"
            "  seed.py            insere dados de exemplo\n"
            "  requirements.txt   dependências do projeto\n"
            "  app/\n"
            "    __init__.py      cria e configura a aplicação\n"
            "    db.py            conexão com o banco de dados\n"
            "    schema.sql       criação das tabelas\n"
            "    categorias.py    CRUD de categorias\n"
            "    livros.py        CRUD de livros\n"
            "    leitores.py      CRUD de leitores\n"
            "    emprestimos.py   empréstimo, devolução e renovação\n"
            "    painel.py        painel inicial\n"
            "    templates/       páginas HTML (Jinja2)\n"
            "    static/          folha de estilo (CSS)\n"
            "  tests/             testes automatizados\n"
            "  docs/              esta documentação", CODIGO)]),
        p("Cada operação de CRUD corresponde a uma rota e a um comando SQL. O Quadro 11 mostra essa "
          "correspondência para a entidade livro; as demais entidades seguem o mesmo padrão."),
        *quadro(11, "Operações de CRUD da entidade livro", [
            ["Operação", "Método e rota", "Comando SQL"],
            ["Criar (Create)", "GET e POST /livros/novo", "INSERT INTO livro"],
            ["Consultar (Read)", "GET /livros/", "SELECT com JOIN em categoria"],
            ["Atualizar (Update)", "GET e POST /livros/&lt;id&gt;/editar", "UPDATE livro"],
            ["Excluir (Delete)", "POST /livros/&lt;id&gt;/excluir", "DELETE FROM livro"],
        ], [3.6, 5.4, 4.4]),
        p("As Figuras 3 a 6 apresentam as principais telas do sistema em funcionamento, com os dados "
          "de exemplo inseridos pelo arquivo seed.py."),
        figura(3, "Painel inicial, com os totais do acervo e os empréstimos em atraso",
               captura("painel.png", 1200, 760)),
        figura(4, "Listagem de livros, com busca, filtro e exemplares disponíveis",
               captura("livros.png", 1200, 760)),
        figura(5, "Formulário de registro de empréstimo", captura("emprestimo-form.png", 1200, 560)),
        figura(6, "Listagem de empréstimos, com filtro por situação", captura("emprestimos.png", 1200, 620)),

        Paragraph("2.7 Testes", TITULO2),
        p("Foram escritos 17 testes automatizados com a biblioteca unittest. Cada teste cria um banco "
          "de dados temporário, simula as requisições do navegador e confere o resultado. Os testes "
          "cobrem o CRUD das quatro entidades, as validações dos formulários e todas as regras de "
          "negócio do Quadro 4, como a recusa de empréstimo sem exemplar disponível, o bloqueio do "
          "leitor em atraso e a proibição de excluir registros com vínculos. Todos os testes são "
          "executados com sucesso pelo comando <i>python -m unittest discover -s tests</i>."),
        PageBreak(),
    ]
    return partes


def conclusao():
    return [
        Paragraph("3 CONCLUSÃO", TITULO1),
        p("O objetivo do projeto foi atingido: o sistema desenvolvido realiza as operações de CRUD "
          "sobre categorias, livros, leitores e empréstimos, comunica-se com um banco de dados "
          "relacional e atende a todos os requisitos funcionais e não funcionais documentados."),
        p("O principal aprendizado foi perceber o valor de documentar antes de programar. Com os "
          "requisitos, os casos de uso e o DER definidos, a implementação tornou-se uma tradução "
          "direta: cada entidade do diagrama virou uma tabela e um módulo do sistema, e cada caso de "
          "uso virou um conjunto de telas e rotas. Sem essa etapa, várias decisões, como o que fazer "
          "ao excluir um livro que já foi emprestado, só apareceriam no meio da programação."),
        p("Na parte de banco de dados, aprendi na prática a importância das chaves estrangeiras e "
          "das restrições. Deixar o próprio banco recusar um dado inconsistente é mais seguro do que "
          "depender apenas das validações da aplicação. Também compreendi por que informações que "
          "podem ser calculadas, como a situação do empréstimo e os exemplares disponíveis, não "
          "devem ser gravadas, e a razão de usar consultas parametrizadas para evitar injeção de SQL."),
        p("No desenvolvimento web, aprendi como funciona o ciclo de requisição e resposta, a "
          "diferença entre os métodos GET e POST, a organização de um projeto Flask em módulos e o "
          "uso de <i>templates</i> para separar a lógica da apresentação. Os testes automatizados "
          "mostraram seu valor ao permitir alterar o código com a segurança de que as regras de "
          "negócio continuavam funcionando."),
        p("Como trabalhos futuros, o sistema pode receber autenticação de usuários com perfis de "
          "acesso, cálculo de multa por atraso, reserva de livros indisponíveis, envio de lembretes "
          "por e-mail e relatórios de livros mais emprestados, além da publicação em um servidor "
          "para acesso pela internet."),
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
