import os

import flet as ft

from app.ui import theme
from app.ui.components.cards import criar_card_stat


def renderizar_dashboard(page, area_conteudo, titulo_pagina, subtitulo,
                         hoje, pasta_raiz, carregar_logs):
    titulo_pagina.value = "Dashboard"
    subtitulo.value = "Visão geral do sistema"

    total_anos = 0
    total_meses = 0
    total_dias = 0
    total_arquivos = 0
    arquivos_hoje = 0
    caminho_hoje = os.path.join(pasta_raiz, str(hoje.year),
                                f"{hoje.month:02d}", f"{hoje.day:02d}")

    if os.path.exists(pasta_raiz):
        for ano in os.listdir(pasta_raiz):
            p_ano = os.path.join(pasta_raiz, ano)
            if not os.path.isdir(p_ano) or not ano.isdigit(): continue
            total_anos += 1
            for mes in os.listdir(p_ano):
                p_mes = os.path.join(p_ano, mes)
                if not os.path.isdir(p_mes): continue
                total_meses += 1
                for dia in os.listdir(p_mes):
                    p_dia = os.path.join(p_mes, dia)
                    if not os.path.isdir(p_dia): continue
                    total_dias += 1
                    for arq in os.listdir(p_dia):
                        if not arq.startswith('.'):
                            total_arquivos += 1

    if os.path.exists(caminho_hoje):
        arquivos_hoje = len([a for a in os.listdir(caminho_hoje)
                             if not a.startswith('.')])

    logs = carregar_logs()[:5]
    itens_log = []
    for log in logs:
        itens_log.append(
            ft.Container(
                bgcolor=theme.BG_CARD,
                border_radius=10,
                padding=12,
                border=ft.Border(
                    top=ft.BorderSide(1, theme.BORDER),
                    right=ft.BorderSide(1, theme.BORDER),
                    bottom=ft.BorderSide(1, theme.BORDER),
                    left=ft.BorderSide(1, theme.BORDER),
                ),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CIRCLE, color=theme.BLUE, size=8),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(log.get("acao",""), color=theme.TEXT_MAIN, size=13),
                                ft.Text(log.get("detalhe","")[:60] if log.get("detalhe") else "",
                                    color=theme.TEXT_MUTED, size=11),
                            ]
                        ),
                        ft.Text(log.get("timestamp",""), color=theme.TEXT_DIM, size=11),
                    ],
                    spacing=12,
                )
            )
        )

    if not itens_log:
        itens_log.append(ft.Text("Nenhuma atividade ainda.", color=theme.TEXT_MUTED, size=13))

    area_conteudo.controls = [
        ft.Row(
            spacing=14,
            controls=[
                criar_card_stat(ft.Icons.FOLDER_ROUNDED,           theme.BLUE, total_anos,     "Anos"),
                criar_card_stat(ft.Icons.CALENDAR_MONTH_ROUNDED,   theme.BLUE, total_meses,    "Meses"),
                criar_card_stat(ft.Icons.TODAY_ROUNDED,            theme.BLUE, total_dias,     "Dias"),
                criar_card_stat(ft.Icons.DESCRIPTION_ROUNDED,      theme.BLUE, total_arquivos, "Contratos total"),
                criar_card_stat(ft.Icons.STAR_ROUNDED,             theme.BLUE, arquivos_hoje,  "Hoje"),
            ]
        ),
        ft.Container(height=10),
        ft.Text("Atividade Recente", size=16, weight=ft.FontWeight.BOLD, color=theme.TEXT_MAIN),
        ft.Container(height=4),
        ft.Column(controls=itens_log, spacing=6),
    ]
    page.update()
