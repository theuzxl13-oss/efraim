"""Geração do PDF da lista de membros (usado pelo painel administrativo)."""

from io import BytesIO
from itertools import groupby

from django.utils import timezone
from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COR_PRINCIPAL = colors.HexColor("#1f3a5f")
COR_LINHA_ALTERNADA = colors.HexColor("#f1f4f8")


def gerar_pdf_membros(membros, filtros_descricao=""):
    """Recebe um iterável de Member (já ordenado por congregação e nome) e
    devolve os bytes de um PDF A4 com a lista agrupada por congregação."""
    buffer = BytesIO()
    agora = timezone.localtime()

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, f"Gerado em {agora:%d/%m/%Y às %H:%M}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title="Lista de membros — Varões Efraim",
        author="Varões Efraim — Setor 46",
    )

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=COR_PRINCIPAL, spaceAfter=4)
    subtitulo = ParagraphStyle("subtitulo", parent=estilos["Normal"], alignment=1, textColor=colors.grey)
    congregacao = ParagraphStyle(
        "congregacao", parent=estilos["Heading2"], textColor=COR_PRINCIPAL, spaceBefore=14, spaceAfter=6
    )
    celula = ParagraphStyle("celula", parent=estilos["Normal"], fontSize=9.5, leading=12)

    historia = [
        Paragraph("Varões Efraim — Setor 46", titulo),
        Paragraph("Lista de membros", subtitulo),
    ]
    if filtros_descricao:
        historia.append(Paragraph(escape(filtros_descricao), subtitulo))
    historia.append(Spacer(1, 0.4 * cm))

    membros = list(membros)
    if not membros:
        historia.append(Paragraph("Nenhum membro encontrado.", estilos["Normal"]))

    larguras = [1.2 * cm, 9.3 * cm, 3.3 * cm, 3.2 * cm]
    for nome_congregacao, grupo in groupby(membros, key=lambda m: m.congregation.name):
        grupo = list(grupo)
        dados = [["Nº", "Nome completo", "Cargo", "Nascimento"]]
        for i, m in enumerate(grupo, start=1):
            dados.append(
                [
                    str(i),
                    Paragraph(escape(m.full_name), celula),
                    m.get_cargo_display(),
                    m.birth_date.strftime("%d/%m/%Y") if m.birth_date else "—",
                ]
            )
        tabela = Table(dados, colWidths=larguras, repeatRows=1)
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cfd6df")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for linha in range(2, len(dados), 2):
            estilo.append(("BACKGROUND", (0, linha), (-1, linha), COR_LINHA_ALTERNADA))
        tabela.setStyle(TableStyle(estilo))

        total = len(grupo)
        cabecalho = Paragraph(escape(nome_congregacao), congregacao)
        if total <= 20:
            # Lista curta: não deixa o nome da congregação sozinho no fim da página.
            historia.append(KeepTogether([cabecalho, tabela]))
        else:
            historia += [cabecalho, tabela]
        historia.append(Spacer(1, 0.15 * cm))
        historia.append(
            Paragraph(f"Total: <b>{total}</b> membro{'s' if total != 1 else ''}", celula)
        )

    if membros:
        historia.append(Spacer(1, 0.6 * cm))
        historia.append(
            Paragraph(f"<b>Total geral: {len(membros)} membro{'s' if len(membros) != 1 else ''}</b>", estilos["Normal"])
        )

    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    return buffer.getvalue()
