from pathlib import Path

import flet as ft

from app.ui import theme


def criar_card_stat(icone, cor, valor, label):
    cor = theme.BLUE
    return ft.Container(
        expand=True,
        bgcolor=theme.BG_CARD,
        border_radius=16,
        padding=24,
        shadow=ft.BoxShadow(blur_radius=12, color=theme.SHADOW_SOFT, offset=ft.Offset(0, 4)),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    width=44, height=44,
                    bgcolor=theme.ICON_BG,
                    border_radius=12,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icone, color=cor, size=22)
                ),
                ft.Text(str(valor), size=28, weight=ft.FontWeight.BOLD, color=theme.BLUE),
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
        shadow=ft.BoxShadow(blur_radius=10, color=theme.SHADOW_SOFT, offset=ft.Offset(0, 3)),
        content=ft.ListTile(
            leading=ft.Container(
                width=42, height=42,
                bgcolor=theme.ICON_BG,
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(icone, color=cor, size=22)
            ),
            title=ft.Text(nome, color=theme.TEXT_MAIN, size=14, weight=ft.FontWeight.W_500),
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
        shadow=ft.BoxShadow(blur_radius=10, color=theme.SHADOW_SOFT, offset=ft.Offset(0, 3)),
        content=ft.ListTile(
            leading=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, color=theme.BLUE),
            title=ft.Text("Voltar", color=theme.TEXT_MAIN),
        )
    )


def criar_item_arquivo(
    nome,
    info,
    caminho_completo,
    on_open,
    on_delete=None,
    on_pdf=None,
    on_sign=None,
    assinatura_status=None,
):
    ext = Path(nome).suffix.lower()
    icone_mapa = {
        ".pdf":  (ft.Icons.PICTURE_AS_PDF_ROUNDED, theme.BLUE),
        ".docx": (ft.Icons.ARTICLE_ROUNDED,        theme.BLUE),
        ".doc":  (ft.Icons.ARTICLE_ROUNDED,        theme.BLUE),
        ".xlsx": (ft.Icons.TABLE_CHART_ROUNDED,    theme.GREEN),
        ".png":  (ft.Icons.IMAGE_ROUNDED,          theme.BLUE_DARK),
        ".jpg":  (ft.Icons.IMAGE_ROUNDED,          theme.BLUE_DARK),
    }
    icone, cor = icone_mapa.get(ext, (ft.Icons.DESCRIPTION_ROUNDED, theme.TEXT_MUTED))
    pode_assinar = (
        on_sign is not None
        and ext == ".pdf"
        and (not assinatura_status or assinatura_status.get("label") not in ("Assinado", "Recusado"))
    )
    detalhes = [ft.Text(info, color=theme.TEXT_MUTED, size=11)]
    if assinatura_status:
        cor_status = assinatura_status["color"]
        detalhes.append(
            ft.Container(
                bgcolor=None,
                border=ft.Border(
                    top=ft.BorderSide(1, cor_status),
                    right=ft.BorderSide(1, cor_status),
                    bottom=ft.BorderSide(1, cor_status),
                    left=ft.BorderSide(1, cor_status),
                ),
                border_radius=6,
                padding=ft.Padding(left=8, right=8, top=3, bottom=3),
                content=ft.Text(
                    assinatura_status["label"],
                    color=cor_status,
                    size=10,
                    weight=ft.FontWeight.W_500,
                ),
            )
        )

    return ft.Container(
        bgcolor=theme.BG_CARD,
        border_radius=14,
        padding=10,
        shadow=ft.BoxShadow(blur_radius=10, color=theme.SHADOW_SOFT, offset=ft.Offset(0, 3)),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=42, height=42,
                    bgcolor=theme.ICON_BG,
                    border_radius=10,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icone, color=cor, size=22)
                ),
                ft.Column(
                    expand=True,
                    spacing=2,
                    controls=[
                        ft.Text(
                            nome,
                            color=theme.TEXT_MAIN,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(spacing=8, controls=detalhes),
                    ],
                ),
                ft.Row(
                    tight=True,
                    spacing=6,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                            icon_color=theme.BLUE,
                            tooltip="Gerar PDF",
                            on_click=lambda e, c=caminho_completo: on_pdf(c) if on_pdf else None,
                            visible=on_pdf is not None and ext in (".doc", ".docx"),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.HOW_TO_REG_ROUNDED,
                            icon_color=theme.BLUE,
                            tooltip="Assinar digitalmente",
                            on_click=lambda e, c=caminho_completo: on_sign(c) if on_sign else None,
                            visible=pode_assinar,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=theme.RED,
                            tooltip="Remover arquivo",
                            on_click=lambda e, c=caminho_completo: on_delete(c) if on_delete else None,
                            visible=on_delete is not None,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                            icon_color=theme.TEXT_DIM,
                            tooltip="Abrir arquivo",
                            on_click=lambda e, c=caminho_completo: on_open(c),
                        ),
                    ],
                ),
            ],
        )
    )


def criar_badge(texto, cor):
    return ft.Container(
        bgcolor=None,
        border=ft.Border(
            top=ft.BorderSide(1, cor),
            right=ft.BorderSide(1, cor),
            bottom=ft.BorderSide(1, cor),
            left=ft.BorderSide(1, cor),
        ),
        border_radius=6,
        padding=ft.Padding(left=8, right=8, top=3, bottom=3),
        content=ft.Text(texto, color=cor, size=10, weight=ft.FontWeight.W_500)
    )
