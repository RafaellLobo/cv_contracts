import os

import flet as ft

from app.services.autentique_service import (
    atualizar_status_assinaturas_autentique,
    listar_contratos_assinados,
)
from app.ui import theme
from app.ui.components.cards import criar_card_stat, criar_item_arquivo


def renderizar_assinados(
    page,
    area_conteudo,
    titulo_pagina,
    subtitulo,
    renderizar_assinados_callback,
    mostrar_snack,
    abrir_arquivo_sistema,
    salvar_log,
):
    titulo_pagina.value = "Assinados"
    subtitulo.value = "Contratos finalizados na Autentique"

    lista = ft.ListView(expand=True, spacing=6, auto_scroll=False)
    contratos = listar_contratos_assinados()

    def abrir_arquivo(caminho):
        try:
            abrir_arquivo_sistema(caminho)
            salvar_log("Arquivo assinado aberto", caminho, status="sucesso")
        except Exception as ex:
            mostrar_snack(f"Não foi possível abrir: {ex}", theme.RED)

    def atualizar_assinados(e=None):
        btn_atualizar.disabled = True
        mostrar_snack("Atualizando assinaturas...", theme.BLUE)
        page.update()

        def executar():
            resultado = atualizar_status_assinaturas_autentique()
            salvar_log(
                "Assinados atualizados",
                resultado["message"],
                status="sucesso" if resultado["success"] else "falha",
                erro="" if resultado["success"] else str(resultado.get("falhas") or ""),
            )
            mostrar_snack(resultado["message"], theme.GREEN if resultado["success"] else theme.RED)
            btn_atualizar.disabled = False
            renderizar_assinados_callback()

        page.run_thread(executar)

    btn_atualizar = ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.REFRESH_ROUNDED, color=theme.BLUE, size=18),
            ft.Text("Atualizar", color=theme.TEXT_MAIN, size=13),
        ]),
        on_click=atualizar_assinados,
        style=ft.ButtonStyle(
            bgcolor={"": theme.BG_CARD},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, theme.BORDER)},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )

    for contrato in contratos:
        caminho = contrato.get("caminho_arquivo") or ""
        erro_download = contrato.get("erro_download_assinado") or ""

        if caminho and os.path.exists(caminho):
            nome = os.path.basename(caminho)
            tipo = "PDF assinado" if caminho.lower().endswith(".pdf") else "Contrato original"
            info = f"{tipo} - {contrato.get('created_at') or 'sem data'}"
            lista.controls.append(
                criar_item_arquivo(
                    nome,
                    info,
                    caminho,
                    abrir_arquivo,
                    assinatura_status={"label": "Assinado", "color": theme.GREEN},
                )
            )
            continue

        lista.controls.append(
            ft.Container(
                bgcolor=theme.BG_CARD,
                border_radius=14,
                padding=14,
                content=ft.Row(
                    spacing=12,
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=theme.RED, size=22),
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(contrato.get("nome") or "Contrato assinado", color=theme.TEXT_MAIN, size=14),
                                ft.Text(
                                    erro_download or "PDF assinado ainda não foi baixado.",
                                    color=theme.TEXT_MUTED,
                                    size=12,
                                ),
                            ],
                        ),
                    ],
                ),
            )
        )

    if not contratos:
        lista.controls.append(
            ft.Container(
                alignment=ft.Alignment(0, 0),
                padding=40,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.TASK_ALT_ROUNDED, color=theme.TEXT_MUTED, size=48),
                        ft.Text("Nenhum contrato assinado ainda.", color=theme.TEXT_MUTED, size=14),
                    ],
                ),
            )
        )

    area_conteudo.controls = [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=14,
                    controls=[
                        criar_card_stat(ft.Icons.TASK_ALT_ROUNDED, theme.BLUE, len(contratos), "Assinados"),
                    ],
                ),
                btn_atualizar,
            ],
        ),
        ft.Container(height=10),
        ft.Container(expand=True, content=lista),
    ]
    page.update()
