import flet as ft

from app.ui import theme


def criar_botao_novo_contrato(on_click):
    return ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.ADD_ROUNDED, color=theme.WHITE, size=18),
            ft.Text("Gerar novo contrato", color=theme.WHITE, size=13, weight=ft.FontWeight.W_500),
        ]),
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={"": theme.BLUE},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )


def criar_botao_calendario(on_click):
    return ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=theme.BLUE, size=18),
            ft.Text("Calendário", color=theme.TEXT_MAIN, size=13),
        ]),
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={"": theme.BG_CARD},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, theme.BORDER)},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )


def criar_botao_pdf(on_click):
    return ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color=theme.PDF_GREEN, size=18),
            ft.Text("Gerar PDF do Dia", color=theme.PDF_GREEN, size=13, weight=ft.FontWeight.W_500),
        ]),
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={"": theme.PDF_BG},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, theme.PDF_BORDER)},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )
