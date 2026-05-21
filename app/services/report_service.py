import datetime
import os

from app.core.paths import caminho_por_data
from app.services.file_service import formatar_tamanho_legivel, listar_itens_visiveis


def gerar_relatorio_pdf_do_dia(data_ref):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER

    nome_arquivo = f"relatorio_{data_ref.strftime('%Y-%m-%d')}.pdf"
    pasta_hoje = caminho_por_data(data_ref)
    os.makedirs(pasta_hoje, exist_ok=True)
    caminho_pdf = os.path.join(pasta_hoje, nome_arquivo)

    doc = SimpleDocTemplate(caminho_pdf, pagesize=A4,
                rightMargin=2*cm, leftMargin=2*cm,
                topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    estilo_titulo = ParagraphStyle('titulo', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor("#1a73e8"),
        spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica-Bold')
    estilo_sub = ParagraphStyle('sub', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor("#666666"),
        spaceAfter=20, alignment=TA_CENTER)
    estilo_rodape = ParagraphStyle('rodape', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor("#aaaaaa"), alignment=TA_CENTER)

    story.append(Paragraph("CV Contracts", estilo_titulo))
    story.append(Paragraph("Automação Jurídica", estilo_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a73e8")))
    story.append(Spacer(1, 0.5*cm))

    meses_pt = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    data_fmt = f"{data_ref.day} de {meses_pt[data_ref.month]} de {data_ref.year}"

    info = [
        ["Data do Relatório:", data_fmt],
        ["Gerado em:", datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")],
        ["Pasta:", pasta_hoje],
    ]
    t_info = Table(info, colWidths=[4*cm, None])
    t_info.setStyle(TableStyle([
        ('FONTNAME',  (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0),(-1,-1), 10),
        ('TEXTCOLOR', (0,0),(0,-1),  colors.HexColor("#555555")),
        ('TEXTCOLOR', (1,0),(1,-1),  colors.HexColor("#222222")),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))

    story.append(Paragraph("Contratos do Dia", ParagraphStyle('sec',
        parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=16, spaceAfter=8, fontName='Helvetica-Bold')))

    try:
        itens = listar_itens_visiveis(pasta_hoje)
        arquivos = [i for i in itens if os.path.isfile(os.path.join(pasta_hoje, i))
                    and i != nome_arquivo]

        if arquivos:
            dados = [["Nome", "Tamanho", "Hora"]]
            for a in arquivos:
                stat = os.stat(os.path.join(pasta_hoje, a))
                tam_str = formatar_tamanho_legivel(stat.st_size)
                hora = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M")
                dados.append([a, tam_str, hora])

            t2 = Table(dados, colWidths=[None, 2.5*cm, 2*cm])
            t2.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,0),  colors.HexColor("#1a73e8")),
                ('TEXTCOLOR',     (0,0),(-1,0),  colors.white),
                ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
                ('FONTSIZE',      (0,0),(-1,-1), 9),
                ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.HexColor("#f8f8f8"), colors.white]),
                ('GRID',          (0,0),(-1,-1), 0.5, colors.HexColor("#dddddd")),
                ('LEFTPADDING',   (0,0),(-1,-1), 8),
                ('RIGHTPADDING',  (0,0),(-1,-1), 8),
                ('TOPPADDING',    (0,0),(-1,-1), 5),
                ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ]))
            story.append(t2)
        else:
            story.append(Paragraph("Nenhum contrato encontrado para esta data.",
                ParagraphStyle('vazio', parent=styles['Normal'],
                    fontSize=10, textColor=colors.HexColor("#888888"))))
    except Exception as err:
        story.append(Paragraph(f"Erro: {err}", styles['Normal']))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Gerado automaticamente pelo CV Contracts • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilo_rodape))

    doc.build(story)
    return {
        "success": True,
        "path": caminho_pdf,
        "error": None,
    }
