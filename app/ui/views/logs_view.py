import flet as ft

from app.ui import theme
from app.ui.components.cards import criar_badge


def renderizar_logs(page, area_conteudo, titulo_pagina, subtitulo, carregar_logs):
    titulo_pagina.value = "Logs"
    subtitulo.value = "Histórico de atividades"

    logs = carregar_logs()
    limite = getattr(page, "_logs_limite", 20)
    logs_visiveis = logs[:limite]

    def cor_status(log):
        s = log.get("status", "")
        e = log.get("erro", "")
        if e:                    return theme.RED
        if s == "sucesso":       return theme.BLUE
        if s == "ignorado":      return theme.YELLOW
        if s == "pendente":      return theme.BLUE_DARK
        acao = log.get("acao","")
        if "PDF" in acao:        return theme.BLUE
        if "Explorador" in acao: return theme.BLUE
        if "App" in acao:        return theme.BLUE_DARK
        return theme.TEXT_MUTED

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
    for log in logs_visiveis:
        cor = cor_status(log)
        icone = icone_status(log)

        badges = []
        if log.get("id_reserva"):
            badges.append(criar_badge(f"Reserva #{log['id_reserva']}", theme.BLUE))
        if log.get("modelo"):
            badges.append(criar_badge(log["modelo"], theme.BLUE_DARK))
        if log.get("status"):
            cores_status = {"sucesso": theme.BLUE, "ignorado": theme.YELLOW,
                            "pendente": theme.BLUE_DARK, "falha": theme.RED}
            badges.append(criar_badge(log["status"].upper(),
                                cores_status.get(log["status"], theme.TEXT_MUTED)))

        detalhes = []
        if log.get("detalhe"):
            detalhes.append(ft.Text(log["detalhe"][:80], color=theme.TEXT_MUTED, size=11))
        if log.get("caminho_pdf"):
            detalhes.append(ft.Row(spacing=4, controls=[
                ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color=theme.BLUE, size=11),
                ft.Text(log["caminho_pdf"][:70], color=theme.TEXT_MUTED, size=10),
            ]))
        if log.get("caminho_docx"):
            detalhes.append(ft.Row(spacing=4, controls=[
                ft.Icon(ft.Icons.ARTICLE_ROUNDED, color=theme.BLUE, size=11),
                ft.Text(log["caminho_docx"][:70], color=theme.TEXT_MUTED, size=10),
            ]))
        if log.get("erro"):
            detalhes.append(ft.Row(spacing=4, controls=[
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=theme.RED, size=11),
                ft.Text(log["erro"][:80], color=theme.RED, size=10),
            ]))

        itens.append(
            ft.Container(
                bgcolor=theme.BG_CARD,
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
                                    ft.Text(log.get("acao",""), color=theme.TEXT_MAIN,
                                            size=13, weight=ft.FontWeight.W_500),
                                    ft.Row(controls=badges, spacing=6) if badges else ft.Container(),
                                ]),
                                ft.Text(log.get("timestamp",""), color=theme.TEXT_DIM, size=11),
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
                    ft.Icon(ft.Icons.HISTORY_ROUNDED, color=theme.TEXT_MUTED, size=48),
                    ft.Text("Nenhuma atividade registrada.", color=theme.TEXT_MUTED, size=14),
                ])
        ))

    if len(logs) > limite:
        def carregar_mais(e):
            page._logs_limite = limite + 20
            renderizar_logs(page, area_conteudo, titulo_pagina, subtitulo, carregar_logs)

        itens.append(ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=12,
            content=ft.ElevatedButton(
                "Exibir logs antigos",
                icon=ft.Icons.EXPAND_MORE_ROUNDED,
                on_click=carregar_mais,
                style=ft.ButtonStyle(
                    bgcolor={"": theme.BG_CARD},
                    color={"": theme.TEXT_MAIN},
                    shape={"": ft.RoundedRectangleBorder(radius=12)},
                    side={"": ft.BorderSide(1, theme.BORDER)},
                )
            )
        ))

    area_conteudo.controls = [
        ft.Container(expand=True,
            content=ft.ListView(controls=itens, spacing=6, expand=True))
    ]
    page.update()
