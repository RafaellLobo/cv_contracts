from pathlib import Path

import flet as ft

from app.ui import theme


def criar_card_stat(icone, cor, valor, label):
    return ft.Container(
        expand=True,
        bgcolor=theme.BG_CARD,
        border_radius=16,
        padding=24,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    width=44, height=44,
                    bgcolor=cor + "22",
                    border_radius=12,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icone, color=cor, size=22)
                ),
                ft.Text(str(valor), size=28, weight=ft.FontWeight.BOLD, color=theme.WHITE),
                ft.Text(label, size=12, color=theme.TEXT_MUTED),
            ]
        )
    )


def criar_item_pasta(nome, icone, cor, on_click_fn, subtexto=""):
    return ft.Container(
        bgcolor=theme.BG_CARD,
        border_radius=14,
        padding=10,
        ink=True,
        on_click=on_click_fn,
        content=ft.ListTile(
            leading=ft.Container(
                width=42, height=42,
                bgcolor=cor + "22",
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(icone, color=cor, size=22)
            ),
            title=ft.Text(nome, color=theme.WHITE, size=14, weight=ft.FontWeight.W_500),
            subtitle=ft.Text(subtexto, color=theme.TEXT_MUTED, size=12) if subtexto else None,
        )
    )


def criar_item_voltar(fn):
    return ft.Container(
        bgcolor=theme.BG_CARD,
        border_radius=12,
        padding=4,
        ink=True,
        on_click=fn,
        content=ft.ListTile(
            leading=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, color=theme.BLUE),
            title=ft.Text("Voltar", color=theme.WHITE),
        )
    )


def criar_item_arquivo(nome, info, caminho_completo, on_open):
    ext = Path(nome).suffix.lower()
    icone_mapa = {
        ".pdf":  (ft.Icons.PICTURE_AS_PDF_ROUNDED, "#e53935"),
        ".docx": (ft.Icons.ARTICLE_ROUNDED,        "#1565c0"),
        ".doc":  (ft.Icons.ARTICLE_ROUNDED,        "#1565c0"),
        ".xlsx": (ft.Icons.TABLE_CHART_ROUNDED,    "#2e7d32"),
        ".png":  (ft.Icons.IMAGE_ROUNDED,          "#7b1fa2"),
        ".jpg":  (ft.Icons.IMAGE_ROUNDED,          "#7b1fa2"),
    }
    icone, cor = icone_mapa.get(ext, (ft.Icons.DESCRIPTION_ROUNDED, "#607d8b"))
    return ft.Container(
        bgcolor=theme.BG_CARD,
        border_radius=14,
        padding=10,
        ink=True,
        on_click=lambda e, c=caminho_completo: on_open(c),
        content=ft.ListTile(
            leading=ft.Container(
                width=42, height=42,
                bgcolor=cor + "22",
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(icone, color=cor, size=22)
            ),
            title=ft.Text(nome, color=theme.WHITE, size=14, weight=ft.FontWeight.W_500),
            subtitle=ft.Text(info, color=theme.TEXT_MUTED, size=11),
            trailing=ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, color=theme.TEXT_DIM, size=16),
        )
    )


def criar_badge(texto, cor):
    return ft.Container(
        bgcolor=cor + "22",
        border_radius=6,
        padding=ft.Padding(left=8, right=8, top=3, bottom=3),
        content=ft.Text(texto, color=cor, size=10, weight=ft.FontWeight.W_500)
    )
