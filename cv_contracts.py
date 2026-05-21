import flet as ft
import datetime


from app.config.settings import CV_BASE_URL, CV_EMAIL, CV_TOKEN, PASTA_RAIZ
from app.core.paths import garantir_estrutura_hoje
from app.repositories.log_repository import carregar_logs, salvar_log
from app.services.cvcrm_client import consultar_reserva
from app.services.file_service import abrir_arquivo_sistema, formatar_tamanho_legivel, listar_itens_visiveis
from app.services.report_service import gerar_relatorio_pdf_do_dia
from app.ui import theme
from app.ui.components.buttons import criar_botao_calendario, criar_botao_novo_contrato, criar_botao_pdf
from app.ui.dialogs.new_contract_dialog import abrir_modal_novo_contrato as abrir_modal_novo_contrato_dialog
from app.ui.components.sidebar import criar_sidebar
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

    # =====================================================
    # MODAL â€” GERAR NOVO CONTRATO
    # =====================================================

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
    subtitulo     = ft.Text("VisÃ£o geral do sistema", color="#B0B3B8", size=13)

    badge_data = ft.Container(
        visible=False,
        bgcolor="#1a3a5c",
        border_radius=20,
        padding=ft.Padding(left=12, right=12, top=6, bottom=6),
        content=ft.Row(
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.CALENDAR_TODAY, color="#4dabf7", size=14),
                ft.Text("", color="#4dabf7", size=12, weight=ft.FontWeight.W_500),
            ]
        )
    )

    area_conteudo = ft.Column(expand=True, spacing=0)

    calendario_container = ft.Container(
        visible=False,
        bgcolor="#1e2023",
        border_radius=16,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=30, color="#00000066", offset=ft.Offset(0, 8)),
        border=ft.Border(
            top=ft.BorderSide(1, "#2d2f33"), bottom=ft.BorderSide(1, "#2d2f33"),
            left=ft.BorderSide(1, "#2d2f33"), right=ft.BorderSide(1, "#2d2f33")
        ),
        width=300,
    )

    overlay_calendario = ft.Container(
        visible=False,
        width=1400, height=800,
        bgcolor="#00000001",
        on_click=lambda e: fechar_calendario(),
    )

    def construir_calendario():
        ano      = mes_calendario["ano"]
        mes      = mes_calendario["mes"]
        nomes    = ["","Janeiro","Fevereiro","MarÃ§o","Abril","Maio","Junho",
                    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        nome_mes = nomes[mes]

        primeiro_dia    = datetime.date(ano, mes, 1)
        dia_semana_ini  = primeiro_dia.weekday()
        ultimo_dia      = (datetime.date(ano, mes % 12 + 1, 1) if mes < 12
                           else datetime.date(ano + 1, 1, 1)) - datetime.timedelta(days=1)

        cabecalho_dias = ft.Row(
            spacing=2,
            controls=[
                ft.Container(width=34, height=28, alignment=ft.Alignment(0,0),
                    content=ft.Text(d, size=11, color="#B0B3B8", weight=ft.FontWeight.W_600))
                for d in ["S","T","Q","Q","S","S","D"]
            ]
        )

        semanas, semana = [], []
        for _ in range(dia_semana_ini):
            semana.append(ft.Container(width=34, height=34))

        for dia in range(1, ultimo_dia.day + 1):
            data_dia   = datetime.date(ano, mes, dia)
            cor_bg     = "#4dabf7" if data_dia == data_selecionada["data"] else (
                         "#1a3a5c" if data_dia == hoje else "transparent")
            cor_txt    = "white" if (data_dia == data_selecionada["data"] or data_dia == hoje) else "#e0e0e0"
            peso       = ft.FontWeight.BOLD if (data_dia == hoje or data_dia == data_selecionada["data"]) else ft.FontWeight.NORMAL

            semana.append(ft.Container(
                width=34, height=34, bgcolor=cor_bg, border_radius=8,
                alignment=ft.Alignment(0,0), ink=True,
                on_click=lambda e, dt=data_dia: selecionar_data(dt),
                content=ft.Text(str(dia), size=13, color=cor_txt, weight=peso)
            ))
            if len(semana) == 7:
                semanas.append(ft.Row(controls=semana, spacing=2))
                semana = []

        if semana:
            while len(semana) < 7:
                semana.append(ft.Container(width=34, height=34))
            semanas.append(ft.Row(controls=semana, spacing=2))

        calendario_container.content = ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(icon=ft.Icons.CHEVRON_LEFT_ROUNDED, icon_color="white",
                            icon_size=20, on_click=lambda e: navegar_mes(-1),
                            style=ft.ButtonStyle(bgcolor={"": "#2d2f33"},
                                shape={"": ft.RoundedRectangleBorder(radius=8)})),
                        ft.Text(f"{nome_mes} {ano}", color="white", size=14, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_color="white",
                            icon_size=20, on_click=lambda e: navegar_mes(1),
                            style=ft.ButtonStyle(bgcolor={"": "#2d2f33"},
                                shape={"": ft.RoundedRectangleBorder(radius=8)})),
                    ]
                ),
                cabecalho_dias,
                ft.Divider(color="#2d2f33", height=1),
                ft.Column(controls=semanas, spacing=2),
                ft.Divider(color="#2d2f33", height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.TextButton("Limpar", on_click=lambda e: limpar_data(),
                            style=ft.ButtonStyle(color="#B0B3B8")),
                        ft.TextButton("Hoje", on_click=lambda e: selecionar_data(hoje),
                            style=ft.ButtonStyle(color="#4dabf7")),
                    ]
                )
            ]
        )
        page.update()

    def navegar_mes(delta):
        mes = mes_calendario["mes"] + delta
        ano = mes_calendario["ano"]
        if mes > 12: mes, ano = 1, ano + 1
        elif mes < 1: mes, ano = 12, ano - 1
        mes_calendario["mes"] = mes
        mes_calendario["ano"] = ano
        construir_calendario()

    def selecionar_data(data):
        data_selecionada["data"] = data
        badge_data.visible = True
        badge_data.content.controls[1].value = data.strftime("%d/%m/%Y")
        fechar_calendario()
        renderizar_explorador()

    def limpar_data():
        data_selecionada["data"] = None
        badge_data.visible = False
        fechar_calendario()
        renderizar_explorador()

    def abrir_calendario(e):
        construir_calendario()
        calendario_container.visible = True
        overlay_calendario.visible   = True
        page.update()

    def fechar_calendario():
        calendario_container.visible = False
        overlay_calendario.visible   = False
        page.update()

    def gerar_pdf_do_dia(e):
        try:
            resultado = gerar_relatorio_pdf_do_dia(data_selecionada["data"] or hoje)
            caminho_pdf = resultado["path"]
            salvar_log("PDF gerado", caminho_pdf,
                       status="sucesso", caminho_pdf=caminho_pdf)
            mostrar_snack(f"âœ“ PDF salvo em: {caminho_pdf}", "#2e7d32")

        except ImportError:
            mostrar_snack("âŒ Instale reportlab: pip install reportlab", "#c62828")
        except Exception as ex:
            mostrar_snack(f"âŒ Erro: {ex}", "#c62828")

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

    # =====================================================
    # SIDEBAR â€” sem Assinar e sem ConfiguraÃ§Ãµes
    # =====================================================

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


ft.app(target=main)
