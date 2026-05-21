import flet as ft

from app.services.contract_generation_service import gerar_contrato_por_reserva


def abrir_modal_novo_contrato(page, salvar_log, consultar_reserva,
                              cv_base_url, cv_email, cv_token, e=None):
    campo_id = ft.TextField(
        label="ID da Reserva",
        hint_text="ex: 12345",
        bgcolor="#2a2b2d",
        border_color="#3d3f42",
        focused_border_color="#4dabf7",
        color="white",
        label_style=ft.TextStyle(color="#B0B3B8"),
        border_radius=10,
        autofocus=True,
    )
    status_text = ft.Text("", color="#B0B3B8", size=12)
    loading = ft.ProgressRing(width=20, height=20, color="#4dabf7", visible=False)
    btn_gerar = ft.ElevatedButton(
        "Consultar e Gerar",
        style=ft.ButtonStyle(
            bgcolor={"": "#1a3a5c"},
            color={"": "white"},
            shape={"": ft.RoundedRectangleBorder(radius=10)},
            padding={"": ft.Padding(left=20, right=20, top=12, bottom=12)},
        )
    )
    btn_cancelar = ft.TextButton(
        "Cancelar",
        style=ft.ButtonStyle(color={"": "#B0B3B8"})
    )

    dialogo = ft.AlertDialog(
        modal=True,
        bgcolor="#1e2023",
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(spacing=10, controls=[
            ft.Container(
                width=36, height=36,
                bgcolor="#1a3a5c",
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color="#4dabf7", size=20)
            ),
            ft.Text("Gerar Novo Contrato", color="white", size=16, weight=ft.FontWeight.W_500),
        ]),
        content=ft.Container(
            width=380,
            content=ft.Column(spacing=14, controls=[
                ft.Text("Informe o ID da reserva para consultar a API do CV CRM.",
                        color="#B0B3B8", size=13),
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

    def on_resultado(data, erro):
        loading.visible = False
        btn_gerar.disabled = False
        reserva_id = campo_id.value.strip()
        if erro:
            status_text.value = f"❌ {erro}"
            status_text.color = "#f87171"
            salvar_log("Erro ao consultar reserva",
                       id_reserva=reserva_id,
                       status="falha", erro=erro)
        else:
            status_text.value = "✓ Reserva encontrada! Gerando contrato..."
            status_text.color = "#34d399"
            salvar_log("Reserva consultada",
                       id_reserva=reserva_id,
                       status="sucesso",
                       detalhe=str(data)[:120])
            resultado = gerar_contrato_por_reserva(reserva_id, data)
            status = resultado.get("status")
            message = resultado.get("message") or "Retorno da geracao nao informado."

            if status == "pendente":
                status_text.value = f"Pendente: {message}"
                status_text.color = "#f59e0b"
                salvar_log("Geracao de contrato pendente",
                           id_reserva=reserva_id,
                           modelo=resultado.get("modelo"),
                           status="pendente",
                           detalhe=message,
                           caminho_docx=resultado.get("caminho_docx"),
                           caminho_pdf=resultado.get("caminho_pdf"),
                           erro=resultado.get("error"))
            elif resultado.get("success"):
                status_text.value = f"Sucesso: {message}"
                status_text.color = "#34d399"
                salvar_log("Contrato gerado",
                           id_reserva=reserva_id,
                           modelo=resultado.get("modelo"),
                           status="sucesso",
                           detalhe=message,
                           caminho_docx=resultado.get("caminho_docx"),
                           caminho_pdf=resultado.get("caminho_pdf"))
            else:
                erro_geracao = resultado.get("error") or message
                status_text.value = f"Erro: {message}"
                status_text.color = "#f87171"
                salvar_log("Erro ao gerar contrato",
                           id_reserva=reserva_id,
                           modelo=resultado.get("modelo"),
                           status="falha",
                           detalhe=message,
                           caminho_docx=resultado.get("caminho_docx"),
                           caminho_pdf=resultado.get("caminho_pdf"),
                           erro=erro_geracao)
        page.update()

    def on_gerar(e):
        reserva_id = campo_id.value.strip()
        if not reserva_id:
            status_text.value = "⚠ Informe o ID da reserva."
            status_text.color = "#f59e0b"
            page.update()
            return
        if not cv_email or not cv_token or not cv_base_url:
            status_text.value = "⚠ Configure o .env com CV_BASE_URL, CV_EMAIL e CV_TOKEN."
            status_text.color = "#f59e0b"
            page.update()
            return
        loading.visible = True
        btn_gerar.disabled = True
        status_text.value = "Consultando API..."
        status_text.color = "#B0B3B8"
        page.update()
        consultar_reserva(reserva_id, on_resultado)

    btn_gerar.on_click = on_gerar
    btn_cancelar.on_click = fechar

    if hasattr(page, "show_dialog"):
        page.show_dialog(dialogo)
    else:
        page.dialog = dialogo
        dialogo.open = True
        page.update()
