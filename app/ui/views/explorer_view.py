import datetime
import os
import shutil

import flet as ft

from app.ui.components.cards import criar_item_arquivo, criar_item_pasta, criar_item_voltar


def renderizar_explorador(page, area_conteudo, titulo_pagina, subtitulo,
                          hoje, nivel_atual, data_selecionada,
                          renderizar_explorador_callback, mostrar_snack,
                          pasta_raiz, abrir_arquivo_sistema,
                          formatar_tamanho_legivel, listar_itens_visiveis,
                          salvar_log):
    titulo_pagina.value = "Explorador"
    subtitulo.value = "Contratos organizados por data"
    nivel = nivel_atual["nivel"]

    lista = ft.ListView(expand=True, spacing=6, auto_scroll=False)

    def importar_arquivo(e):
        def on_result(result: ft.FilePickerResultEvent):
            if not result.files:
                return
            pasta_destino = os.path.join(
                pasta_raiz, str(hoje.year),
                f"{hoje.month:02d}", f"{hoje.day:02d}"
            )
            os.makedirs(pasta_destino, exist_ok=True)
            importados = 0
            for f in result.files:
                try:
                    destino = os.path.join(pasta_destino, os.path.basename(f.path))
                    shutil.copy2(f.path, destino)
                    salvar_log("Arquivo importado", os.path.basename(f.path), status="sucesso",
                               caminho_docx=destino if f.path.endswith((".doc",".docx")) else "",
                               caminho_pdf=destino if f.path.endswith(".pdf") else "")
                    importados += 1
                except Exception as ex:
                    salvar_log("Erro ao importar", str(ex), status="falha", erro=str(ex))
            mostrar_snack(f"✓ {importados} arquivo(s) importado(s) para hoje", "#2e7d32")
            nivel_atual.update({"nivel":"dia",
                                "ano": hoje.year,
                                "mes": hoje.month,
                                "dia": hoje.day})
            renderizar_explorador_callback()

        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allow_multiple=True)

    def abrir_arquivo(caminho):
        try:
            abrir_arquivo_sistema(caminho)
            salvar_log("Arquivo aberto", caminho, status="sucesso")
        except Exception as ex:
            mostrar_snack(f"❌ Não foi possível abrir: {ex}", "#c62828")

    partes = ["Contratos"]
    if nivel_atual["ano"]:  partes.append(str(nivel_atual["ano"]))
    if nivel_atual["mes"]:  partes.append(f"{nivel_atual['mes']:02d}")
    if nivel_atual["dia"]:  partes.append(f"{nivel_atual['dia']:02d}")

    breadcrumb_controls = []
    for i, parte in enumerate(partes):
        breadcrumb_controls.append(
            ft.Text(parte, color="white" if i == len(partes)-1 else "#B0B3B8", size=13)
        )
        if i < len(partes) - 1:
            breadcrumb_controls.append(
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color="#555", size=16)
            )

    breadcrumb = ft.Container(
        bgcolor="#242526",
        border_radius=14,
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        content=ft.Row(controls=breadcrumb_controls, spacing=4)
    )

    if nivel == "raiz":
        if os.path.exists(pasta_raiz):
            anos = sorted([a for a in os.listdir(pasta_raiz)
                            if os.path.isdir(os.path.join(pasta_raiz, a)) and a.isdigit()],
                           reverse=True)
            for ano in anos:
                p = os.path.join(pasta_raiz, ano)
                qtd = sum(len(os.listdir(os.path.join(p, m, d)))
                          for m in os.listdir(p) if os.path.isdir(os.path.join(p, m))
                          for d in os.listdir(os.path.join(p, m)) if os.path.isdir(os.path.join(p, m, d)))
                def abrir_ano(e, a=int(ano)):
                    nivel_atual.update({"nivel":"ano","ano":a,"mes":None,"dia":None})
                    renderizar_explorador_callback()
                lista.controls.append(
                    criar_item_pasta(ano, ft.Icons.FOLDER_ROUNDED, "#4dabf7",
                               abrir_ano, f"{qtd} arquivo(s)"))
        if not lista.controls:
            lista.controls.append(ft.Container(
                alignment=ft.Alignment(0, 0), padding=40,
                content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OFF_ROUNDED, color="#555", size=48),
                        ft.Text("Nenhum contrato ainda.", color="#555", size=14),
                    ])
            ))

    elif nivel == "ano":
        lista.controls.append(criar_item_voltar(lambda e: (
            nivel_atual.update({"nivel":"raiz","ano":None,"mes":None,"dia":None}),
            renderizar_explorador_callback()
        )))
        p_ano = os.path.join(pasta_raiz, str(nivel_atual["ano"]))
        meses_nomes = ["","Jan","Fev","Mar","Abr","Mai","Jun",
                       "Jul","Ago","Set","Out","Nov","Dez"]
        if os.path.exists(p_ano):
            meses = sorted([m for m in os.listdir(p_ano)
                             if os.path.isdir(os.path.join(p_ano, m)) and m.isdigit()])
            for mes in meses:
                p_mes = os.path.join(p_ano, mes)
                qtd = sum(len(os.listdir(os.path.join(p_mes, d)))
                            for d in os.listdir(p_mes)
                            if os.path.isdir(os.path.join(p_mes, d)))
                nm = meses_nomes[int(mes)] if int(mes) <= 12 else mes
                def abrir_mes(e, m=int(mes)):
                    nivel_atual.update({"nivel":"mes","mes":m,"dia":None})
                    renderizar_explorador_callback()
                lista.controls.append(
                    criar_item_pasta(f"{mes} — {nm}", ft.Icons.CALENDAR_MONTH_ROUNDED, "#a78bfa",
                               abrir_mes, f"{qtd} arquivo(s)"))

    elif nivel == "mes":
        lista.controls.append(criar_item_voltar(lambda e: (
            nivel_atual.update({"nivel":"ano","mes":None,"dia":None}),
            renderizar_explorador_callback()
        )))
        p_mes = os.path.join(pasta_raiz, str(nivel_atual["ano"]),
                              f"{nivel_atual['mes']:02d}")
        if os.path.exists(p_mes):
            dias = sorted([d for d in os.listdir(p_mes)
                            if os.path.isdir(os.path.join(p_mes, d)) and d.isdigit()])
            for dia in dias:
                p_dia = os.path.join(p_mes, dia)
                qtd = len([a for a in os.listdir(p_dia) if not a.startswith('.')])
                data_dia = datetime.date(nivel_atual["ano"], nivel_atual["mes"], int(dia))
                label = " — Hoje" if data_dia == hoje else ""
                def abrir_dia(e, d=int(dia)):
                    nivel_atual.update({"nivel":"dia","dia":d})
                    renderizar_explorador_callback()
                lista.controls.append(
                    criar_item_pasta(f"Dia {dia}{label}", ft.Icons.TODAY_ROUNDED, "#34d399",
                               abrir_dia, f"{qtd} arquivo(s)"))

    elif nivel == "dia":
        lista.controls.append(criar_item_voltar(lambda e: (
            nivel_atual.update({"nivel":"mes","dia":None}),
            renderizar_explorador_callback()
        )))
        p_dia = os.path.join(pasta_raiz, str(nivel_atual["ano"]),
                              f"{nivel_atual['mes']:02d}", f"{nivel_atual['dia']:02d}")
        if os.path.exists(p_dia):
            arquivos = listar_itens_visiveis(p_dia)

            if data_selecionada["data"]:
                data_fil = data_selecionada["data"]
                arquivos = [a for a in arquivos if datetime.date.fromtimestamp(
                    os.path.getmtime(os.path.join(p_dia, a))) == data_fil]

            if arquivos:
                for arq in arquivos:
                    try:
                        caminho_arq = os.path.join(p_dia, arq)
                        stat = os.stat(caminho_arq)
                        tam_str = formatar_tamanho_legivel(stat.st_size)
                        hora = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                        info = f"{tam_str} • {hora}"
                    except:
                        caminho_arq = os.path.join(p_dia, arq)
                        info = "Arquivo"
                    lista.controls.append(criar_item_arquivo(arq, info, caminho_arq, abrir_arquivo))
            else:
                lista.controls.append(ft.Container(
                    alignment=ft.Alignment(0, 0), padding=40,
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.INBOX_ROUNDED, color="#555", size=48),
                            ft.Text("Nenhum arquivo nesta pasta.", color="#555", size=14),
                        ])
                ))

    salvar_log("Explorador", f"Nível: {nivel}")

    btn_importar = ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, color="#4dabf7", size=18),
            ft.Text("Importar arquivo", color="white", size=13),
        ]),
        on_click=importar_arquivo,
        style=ft.ButtonStyle(
            bgcolor={"": "#1a3a5c"},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, "#2d5c8c")},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )

    area_conteudo.controls = [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                breadcrumb,
                btn_importar,
            ]
        ),
        ft.Container(height=6),
        ft.Container(expand=True, content=lista),
    ]
    page.update()
