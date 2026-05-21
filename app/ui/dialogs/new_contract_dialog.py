import flet as ft

from app.ui import theme
from app.services.contract_generation_service import (
    gerar_contrato_por_reserva,
    preparar_campos_contrato,
)


def abrir_modal_novo_contrato(page, salvar_log, consultar_reserva,
                              cv_base_url, cv_email, cv_token, e=None):
    campo_id = ft.TextField(
        label="ID da Reserva",
        hint_text="ex: 12345",
        bgcolor=theme.BG_CARD,
        border_color=theme.BORDER,
        focused_border_color=theme.BLUE,
        color=theme.TEXT_MAIN,
        label_style=ft.TextStyle(color=theme.TEXT_MUTED),
        border_radius=10,
        autofocus=True,
        height=54,
    )
    status_text = ft.Text("", color=theme.TEXT_MUTED, size=12)
    loading = ft.ProgressRing(width=20, height=20, color=theme.BLUE, visible=False)
    btn_gerar = ft.ElevatedButton(
        "Consultar e Gerar",
        style=ft.ButtonStyle(
            bgcolor={"": theme.BLUE},
            color={"": "white"},
            shape={"": ft.RoundedRectangleBorder(radius=10)},
            padding={"": ft.Padding(left=20, right=20, top=12, bottom=12)},
        )
    )
    btn_cancelar = ft.TextButton(
        "Cancelar",
        style=ft.ButtonStyle(color={"": theme.TEXT_MUTED})
    )

    dialogo = ft.AlertDialog(
        modal=True,
        bgcolor=theme.BG_PANEL,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(spacing=10, controls=[
            ft.Container(
                width=36, height=36,
                bgcolor=theme.SOFT_BG,
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=theme.BLUE, size=20)
            ),
            ft.Text("Gerar Novo Contrato", color=theme.TEXT_MAIN, size=16, weight=ft.FontWeight.W_500),
        ]),
        content=ft.Container(
            width=520,
            content=ft.Column(spacing=14, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, controls=[
                ft.Text("Informe o ID da reserva para consultar a API do CV CRM.",
                        color=theme.TEXT_MUTED, size=13),
                campo_id,
                ft.Row(spacing=10, controls=[loading, status_text]),
            ])
        ),
        actions=[btn_cancelar, btn_gerar],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def fechar(e=None):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        else:
            dialogo.open = False
        page.update()

    def mostrar_dialogo_sucesso(mensagem, caminho_docx=None):
        sucesso_dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_PANEL,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text("Contrato gerado", color=theme.TEXT_MAIN, size=16, weight=ft.FontWeight.W_500),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[
                    ft.Text(mensagem, color=theme.GREEN, size=13),
                    ft.Text(caminho_docx or "", color=theme.TEXT_MUTED, size=12, selectable=True),
                ],
            ),
            actions=[
                ft.TextButton(
                    "OK",
                    style=ft.ButtonStyle(color={"": theme.TEXT_MUTED}),
                    on_click=lambda e: fechar_dialogo_sucesso(sucesso_dialogo),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(page, "show_dialog"):
            page.show_dialog(sucesso_dialogo)
        else:
            page.dialog = sucesso_dialogo
            sucesso_dialogo.open = True

    def fechar_dialogo_sucesso(sucesso_dialogo):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        else:
            sucesso_dialogo.open = False
        page.update()

    def mostrar_resultado_geracao(resultado, reserva_id, status_control):
        status = resultado.get("status")
        message = resultado.get("message") or "Retorno da geracao nao informado."

        if status == "pendente":
            status_control.value = f"Pendente: {message}"
            status_control.color = theme.YELLOW
            salvar_log("Geracao de contrato pendente",
                       id_reserva=reserva_id,
                       modelo=resultado.get("modelo"),
                       status="pendente",
                       detalhe=message,
                       caminho_docx=resultado.get("caminho_docx"),
                       caminho_pdf=resultado.get("caminho_pdf"),
                       erro=resultado.get("error"))
        elif resultado.get("success"):
            status_control.value = f"Sucesso: {message}"
            status_control.color = theme.GREEN
            salvar_log("Contrato gerado",
                       id_reserva=reserva_id,
                       modelo=resultado.get("modelo"),
                       status="sucesso",
                       detalhe=message,
                       caminho_docx=resultado.get("caminho_docx"),
                       caminho_pdf=resultado.get("caminho_pdf"))
        else:
            erro_geracao = resultado.get("error") or message
            status_control.value = f"Erro: {message}"
            status_control.color = theme.RED
            salvar_log("Erro ao gerar contrato",
                       id_reserva=reserva_id,
                       modelo=resultado.get("modelo"),
                       status="falha",
                       detalhe=message,
                       caminho_docx=resultado.get("caminho_docx"),
                       caminho_pdf=resultado.get("caminho_pdf"),
                       erro=erro_geracao)

    def abrir_tela_campos(reserva_id, reserva_data, preparacao):
        campos_inputs = []
        campos_faltantes = [campo for campo in preparacao["campos"] if campo["missing"]]
        for campo in preparacao["campos"]:
            input_campo = ft.TextField(
                label=campo["label"],
                value=campo["value"],
                hint_text=campo["original"] if campo["missing"] else "",
                bgcolor=theme.BG_CARD,
                border_color=theme.YELLOW if campo["missing"] else theme.BORDER,
                focused_border_color=theme.BLUE,
                color=theme.TEXT_MAIN,
                label_style=ft.TextStyle(
                    color=theme.YELLOW if campo["missing"] else theme.TEXT_MUTED
                ),
                border_radius=10,
                height=52,
            )
            campos_inputs.append((campo, input_campo))

        status_campos = ft.Text("", color=theme.TEXT_MUTED, size=12, expand=True)
        loading_campos = ft.ProgressRing(width=20, height=20, color=theme.BLUE, visible=False)
        btn_confirmar = ft.ElevatedButton(
            "Gerar Contrato",
            style=ft.ButtonStyle(
                bgcolor={"": theme.BLUE},
                color={"": "white"},
                shape={"": ft.RoundedRectangleBorder(radius=10)},
                padding={"": ft.Padding(left=20, right=20, top=12, bottom=12)},
            )
        )
        btn_voltar = ft.TextButton(
            "Cancelar",
            style=ft.ButtonStyle(color={"": theme.TEXT_MUTED})
        )

        campos_dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_PANEL,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text("Dados do Contrato", color=theme.TEXT_MAIN, size=16, weight=ft.FontWeight.W_500),
            content=ft.Container(
                width=860,
                height=560,
                content=ft.Column(
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Row(spacing=10, controls=[loading_campos, status_campos]),
                        ft.Container(
                            expand=True,
                            content=ft.Column(
                                spacing=12,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                scroll=ft.ScrollMode.AUTO,
                                controls=[
                                    ft.Text("Revise os dados retornados pela API. Campos com borda amarela estão faltantes e podem ficar em branco.",
                                            color=theme.TEXT_MUTED, size=13),
                                    ft.Text("Nenhum dado faltante encontrado.",
                                            color=theme.TEXT_MUTED, size=13,
                                            visible=not campos_faltantes),
                                    *[input_campo for _, input_campo in campos_inputs],
                                ]
                            )
                        ),
                    ]
                )
            ),
            actions=[btn_voltar, btn_confirmar],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def fechar_campos(e=None):
            if hasattr(page, "pop_dialog"):
                page.pop_dialog()
            else:
                campos_dialogo.open = False
            page.update()

        def confirmar_geracao(e):
            dados_contrato = preparacao["dados"].copy()
            for campo, input_campo in campos_inputs:
                valor = (input_campo.value or "").strip()
                if valor:
                    dados_contrato[campo["marcador"]] = valor

            loading_campos.visible = True
            btn_confirmar.disabled = True
            status_campos.value = "Gerando contrato..."
            status_campos.color = theme.TEXT_MUTED
            page.update()

            resultado = gerar_contrato_por_reserva(reserva_id, reserva_data, dados_contrato)

            loading_campos.visible = False
            btn_confirmar.disabled = False
            mostrar_resultado_geracao(resultado, reserva_id, status_campos)
            if resultado.get("success"):
                if hasattr(page, "pop_dialog"):
                    page.pop_dialog()
                else:
                    campos_dialogo.open = False
                mostrar_dialogo_sucesso(
                    "Contrato gerado com sucesso!",
                    resultado.get("caminho_docx"),
                )
            page.update()

        btn_confirmar.on_click = confirmar_geracao
        btn_voltar.on_click = fechar_campos

        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
            page.show_dialog(campos_dialogo)
        else:
            dialogo.open = False
            page.dialog = campos_dialogo
            campos_dialogo.open = True
            page.update()

    def on_resultado(data, erro):
        loading.visible = False
        btn_gerar.disabled = False
        reserva_id = campo_id.value.strip()
        if erro:
            status_text.value = f"❌ {erro}"
            status_text.color = theme.RED
            salvar_log("Erro ao consultar reserva",
                       id_reserva=reserva_id,
                       status="falha", erro=erro)
        else:
            status_text.value = "✓ Reserva encontrada! Gerando contrato..."
            status_text.color = theme.GREEN
            salvar_log("Reserva consultada",
                       id_reserva=reserva_id,
                       status="sucesso",
                       detalhe=str(data)[:120])
            preparacao = preparar_campos_contrato(data)
            if preparacao.get("success"):
                abrir_tela_campos(reserva_id, data, preparacao)
                return

            status_text.value = f"Erro: {preparacao.get('message')}"
            status_text.color = theme.RED
            salvar_log("Erro ao preparar dados do contrato",
                       id_reserva=reserva_id,
                       status="falha",
                       erro=preparacao.get("error"))
        page.update()

    async def on_resultado_async(data, erro):
        on_resultado(data, erro)

    def on_gerar(e):
        reserva_id = campo_id.value.strip()
        if not reserva_id:
            status_text.value = "⚠ Informe o ID da reserva."
            status_text.color = theme.YELLOW
            page.update()
            return
        if not cv_email or not cv_token or not cv_base_url:
            status_text.value = "⚠ Configure o .env com CV_BASE_URL, CV_EMAIL e CV_TOKEN."
            status_text.color = theme.YELLOW
            page.update()
            return
        loading.visible = True
        btn_gerar.disabled = True
        status_text.value = "Consultando API..."
        status_text.color = theme.TEXT_MUTED
        page.update()
        def callback_consulta(data, erro):
            page.run_task(on_resultado_async, data, erro)

        consultar_reserva(reserva_id, callback_consulta)

    btn_gerar.on_click = on_gerar
    btn_cancelar.on_click = fechar

    if hasattr(page, "show_dialog"):
        page.show_dialog(dialogo)
    else:
        page.dialog = dialogo
        dialogo.open = True
        page.update()
