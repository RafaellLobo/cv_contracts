import datetime

import flet as ft

from app.config.settings import CV_BASE_URL, CV_EMAIL, CV_TOKEN, PASTA_RAIZ
from app.core.paths import garantir_estrutura_hoje
from app.repositories.log_repository import carregar_logs, salvar_log
from app.services.cvcrm_client import consultar_reserva
from app.services.file_service import abrir_arquivo_sistema, formatar_tamanho_legivel, listar_itens_visiveis
from app.services.report_service import gerar_relatorio_pdf_do_dia
from app.ui import theme
from app.ui.components.buttons import criar_botao_calendario, criar_botao_novo_contrato, criar_botao_pdf
from app.ui.components.calendar import create_calendar_controls
from app.ui.components.sidebar import criar_sidebar
from app.ui.dialogs.new_contract_dialog import abrir_modal_novo_contrato as abrir_modal_novo_contrato_dialog
from app.ui.views.dashboard_view import renderizar_dashboard as renderizar_dashboard_view
from app.ui.views.explorer_view import renderizar_explorador as renderizar_explorador_view
from app.ui.views.logs_view import renderizar_logs as renderizar_logs_view


def main(page: ft.Page):

    page.title        = "CV Contracts"
    page.window_width  = 1400
    page.window_height = 800
    page.theme_mode   = ft.ThemeMode.DARK
    page.padding      = 0
    page.bgcolor      = theme.BG_MAIN

    garantir_estrutura_hoje()
    salvar_log("App iniciado")

    hoje = datetime.date.today()
    data_selecionada  = {"data": None}
    mes_calendario    = {"ano": hoje.year, "mes": hoje.month}
    nivel_atual       = {"nivel": "raiz", "ano": None, "mes": None, "dia": None}

    def mostrar_snack(mensagem, cor="#4dabf7"):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensagem, color="white"),
            bgcolor=cor,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    def abrir_modal_novo_contrato(e=None):
        abrir_modal_novo_contrato_dialog(
            page=page,
            salvar_log=salvar_log,
            consultar_reserva=consultar_reserva,
            cv_base_url=CV_BASE_URL,
            cv_email=CV_EMAIL,
            cv_token=CV_TOKEN,
            e=e,
        )

    titulo_pagina = ft.Text("Contratos", size=26, weight=ft.FontWeight.BOLD, color="white")
    subtitulo     = ft.Text("Visão geral do sistema", color="#B0B3B8", size=13)

    area_conteudo = ft.Column(expand=True, spacing=0)

    def gerar_pdf_do_dia(e):
        try:
            resultado = gerar_relatorio_pdf_do_dia(data_selecionada["data"] or hoje)
            caminho_pdf = resultado["path"]
            salvar_log("PDF gerado", caminho_pdf,
                       status="sucesso", caminho_pdf=caminho_pdf)
            mostrar_snack(f"✓ PDF salvo em: {caminho_pdf}", "#2e7d32")

        except ImportError:
            mostrar_snack("❌ Instale reportlab: pip install reportlab", "#c62828")
        except Exception as ex:
            mostrar_snack(f"❌ Erro: {ex}", "#c62828")

    def renderizar_dashboard():
        renderizar_dashboard_view(
            page=page,
            area_conteudo=area_conteudo,
            titulo_pagina=titulo_pagina,
            subtitulo=subtitulo,
            hoje=hoje,
            pasta_raiz=PASTA_RAIZ,
            carregar_logs=carregar_logs,
        )

    def renderizar_explorador():
        renderizar_explorador_view(
            page=page,
            area_conteudo=area_conteudo,
            titulo_pagina=titulo_pagina,
            subtitulo=subtitulo,
            hoje=hoje,
            nivel_atual=nivel_atual,
            data_selecionada=data_selecionada,
            renderizar_explorador_callback=renderizar_explorador,
            mostrar_snack=mostrar_snack,
            pasta_raiz=PASTA_RAIZ,
            abrir_arquivo_sistema=abrir_arquivo_sistema,
            formatar_tamanho_legivel=formatar_tamanho_legivel,
            listar_itens_visiveis=listar_itens_visiveis,
            salvar_log=salvar_log,
        )

    def renderizar_logs():
        renderizar_logs_view(
            page=page,
            area_conteudo=area_conteudo,
            titulo_pagina=titulo_pagina,
            subtitulo=subtitulo,
            carregar_logs=carregar_logs,
        )

    def trocar_pagina(nome):
        if   nome == "Dashboard":  renderizar_dashboard()
        elif nome == "Explorador": renderizar_explorador()
        elif nome == "Logs":       renderizar_logs()

    calendario = create_calendar_controls(
        page=page,
        hoje=hoje,
        data_selecionada=data_selecionada,
        mes_calendario=mes_calendario,
        renderizar_explorador=renderizar_explorador,
    )
    badge_data = calendario["badge_data"]
    calendario_container = calendario["calendario_container"]
    overlay_calendario = calendario["overlay_calendario"]
    abrir_calendario = calendario["abrir_calendario"]

    sidebar = criar_sidebar(trocar_pagina)
    btn_novo_contrato = criar_botao_novo_contrato(abrir_modal_novo_contrato)
    btn_calendario = criar_botao_calendario(abrir_calendario)
    btn_pdf = criar_botao_pdf(gerar_pdf_do_dia)

    conteudo = ft.Container(
        expand=True,
        padding=28,
        content=ft.Column(
            expand=True, spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(spacing=2, controls=[titulo_pagina, subtitulo]),
                        ft.Row(spacing=10, controls=[badge_data, btn_calendario, btn_pdf, btn_novo_contrato])
                    ]
                ),
                ft.Divider(color="#2d2f33", height=1),
                ft.Container(expand=True, content=area_conteudo),
            ]
        )
    )

    stack_principal = ft.Stack(
        expand=True,
        controls=[
            ft.Row(controls=[sidebar, conteudo], expand=True),
            overlay_calendario,
            ft.Container(content=calendario_container, right=30, top=90, visible=True),
        ]
    )

    page.add(stack_principal)
    renderizar_dashboard()
