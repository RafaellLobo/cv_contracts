import flet as ft

from app.ui.components.cards import criar_badge


def renderizar_logs(page, area_conteudo, titulo_pagina, subtitulo, carregar_logs):
    titulo_pagina.value = "Logs"
    subtitulo.value = "Histórico de atividades"

    logs = carregar_logs()

    def cor_status(log):
        s = log.get("status", "")
        e = log.get("erro", "")
        if e:                    return "#f87171"   # vermelho — erro
        if s == "sucesso":       return "#34d399"   # verde
        if s == "ignorado":      return "#f59e0b"   # amarelo
        if s == "pendente":      return "#a78bfa"   # roxo
        acao = log.get("acao","")
        if "PDF" in acao:        return "#34d399"
        if "Explorador" in acao: return "#4dabf7"
        if "App" in acao:        return "#a78bfa"
        return "#B0B3B8"

    def icone_status(log):
        s = log.get("status", "")
        e = log.get("erro", "")
        if e:                    return ft.Icons.ERROR_OUTLINE_ROUNDED
        if s == "sucesso":       return ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
        if s == "ignorado":      return ft.Icons.REMOVE_CIRCLE_OUTLINE_ROUNDED
        if s == "pendente":      return ft.Icons.HOURGLASS_EMPTY_ROUNDED
        acao = log.get("acao","")
        if "PDF" in acao:        return ft.Icons.PICTURE_AS_PDF_ROUNDED
        if "Explorador" in acao: return ft.Icons.FOLDER_ROUNDED
        if "App" in acao:        return ft.Icons.POWER_SETTINGS_NEW_ROUNDED
        return ft.Icons.CIRCLE

    itens = []
    for log in logs:
        cor = cor_status(log)
        icone = icone_status(log)

        badges = []
        if log.get("id_reserva"):
            badges.append(criar_badge(f"Reserva #{log['id_reserva']}", "#4dabf7"))
        if log.get("modelo"):
            badges.append(criar_badge(log["modelo"], "#a78bfa"))
        if log.get("status"):
            cores_status = {"sucesso": "#34d399", "ignorado": "#f59e0b",
                            "pendente": "#a78bfa", "falha": "#f87171"}
            badges.append(criar_badge(log["status"].upper(),
                                cores_status.get(log["status"], "#B0B3B8")))

        detalhes = []
        if log.get("detalhe"):
            detalhes.append(ft.Text(log["detalhe"][:80], color="#888", size=11))
        if log.get("caminho_pdf"):
            detalhes.append(ft.Row(spacing=4, controls=[
                ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color="#e53935", size=11),
                ft.Text(log["caminho_pdf"][:70], color="#666", size=10),
            ]))
        if log.get("caminho_docx"):
            detalhes.append(ft.Row(spacing=4, controls=[
                ft.Icon(ft.Icons.ARTICLE_ROUNDED, color="#1565c0", size=11),
                ft.Text(log["caminho_docx"][:70], color="#666", size=10),
            ]))
        if log.get("erro"):
            detalhes.append(ft.Row(spacing=4, controls=[
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="#f87171", size=11),
                ft.Text(log["erro"][:80], color="#f87171", size=10),
            ]))

        itens.append(
            ft.Container(
                bgcolor="#242526",
                border_radius=12,
                padding=14,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.Container(
                                    width=36, height=36,
                                    bgcolor=cor + "22",
                                    border_radius=8,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(icone, color=cor, size=18)
                                ),
                                ft.Column(spacing=2, expand=True, controls=[
                                    ft.Text(log.get("acao",""), color="white",
                                            size=13, weight=ft.FontWeight.W_500),
                                    ft.Row(controls=badges, spacing=6) if badges else ft.Container(),
                                ]),
                                ft.Text(log.get("timestamp",""), color="#555", size=11),
                            ]
                        ),
                        *detalhes,
                    ]
                )
            )
        )

    if not itens:
        itens.append(ft.Container(
            alignment=ft.Alignment(0, 0), padding=40,
            content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.HISTORY_ROUNDED, color="#555", size=48),
                    ft.Text("Nenhuma atividade registrada.", color="#555", size=14),
                ])
        ))

    area_conteudo.controls = [
        ft.Container(expand=True,
            content=ft.ListView(controls=itens, spacing=6, expand=True))
    ]
    page.update()
