import flet as ft

from app.ui import theme


def criar_item_sidebar(icone, texto, on_click):
    return ft.Container(
        border_radius=12, ink=True,
        padding=ft.Padding(left=14, right=14, top=11, bottom=11),
        on_click=lambda e, t=texto: on_click(t),
        bgcolor=theme.BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, "#0F172A0F"),
            right=ft.BorderSide(1, "#0F172A0F"),
            bottom=ft.BorderSide(1, "#0F172A0F"),
            left=ft.BorderSide(1, "#0F172A0F"),
        ),
        content=ft.Row(
            spacing=12,
            controls=[
                ft.Icon(icone, color=theme.TEXT_MUTED, size=20),
                ft.Text(texto, color=theme.TEXT_MUTED, size=14)
            ]
        )
    )


def criar_sidebar(on_item_click):
    itens_sidebar = [
        (ft.Icons.DASHBOARD_ROUNDED,    "Dashboard"),
        (ft.Icons.FOLDER_ROUNDED,       "Explorador"),
        (ft.Icons.TASK_ALT_ROUNDED,     "Assinados"),
        (ft.Icons.RECEIPT_LONG_ROUNDED, "Logs"),
    ]

    return ft.Container(
        width=250,
        bgcolor=theme.BG_SIDEBAR,
        padding=ft.Padding(left=16, right=16, top=24, bottom=24),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Container(
                    padding=ft.Padding(left=4, right=0, top=0, bottom=4),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Image(src="logo.svg", width=42, height=42),
                            ft.Column(spacing=2, controls=[
                                ft.Text("CV Contracts", size=22, weight=ft.FontWeight.BOLD, color=theme.TEXT_MAIN),
                                ft.Text("Automação Jurídica", color=theme.TEXT_MUTED, size=12),
                            ]),
                        ],
                    )
                ),
                ft.Divider(color=theme.BORDER, height=20),
                *[criar_item_sidebar(ic, txt, on_item_click) for ic, txt in itens_sidebar],
            ]
        )
    )
