import datetime
import os
import shutil
import subprocess

import flet as ft

from app.services.autentique_service import assinar_docx_autentique, status_assinatura_arquivo
from app.ui import theme
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
    termo_pesquisa = nivel_atual.get("pesquisa", "")

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

    def atualizar_explorador(e=None):
        renderizar_explorador_callback()

    def pesquisar_contratos(e):
        nivel_atual["pesquisa"] = campo_pesquisa.value.strip()
        renderizar_explorador_callback()

    def limpar_pesquisa(e):
        nivel_atual["pesquisa"] = ""
        renderizar_explorador_callback()

    def fechar_dialogo(dialogo):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        else:
            dialogo.open = False
        page.update()

    def confirmar_remocao(caminho):
        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_PANEL,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text("Remover documento", color="white", size=16, weight=ft.FontWeight.W_500),
            content=ft.Text(
                f"Deseja realmente excluir {os.path.basename(caminho)}?",
                color=theme.TEXT_MUTED,
                size=13,
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color={"": theme.TEXT_MUTED}),
                    on_click=lambda e: fechar_dialogo(dialogo),
                ),
                ft.ElevatedButton(
                    "Excluir",
                    style=ft.ButtonStyle(
                        bgcolor={"": "#7f1d1d"},
                        color={"": "white"},
                        shape={"": ft.RoundedRectangleBorder(radius=10)},
                    ),
                    on_click=lambda e: remover_arquivo(caminho, dialogo),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(page, "show_dialog"):
            page.show_dialog(dialogo)
        else:
            page.dialog = dialogo
            dialogo.open = True
            page.update()

    def remover_arquivo(caminho, dialogo=None):
        try:
            os.remove(caminho)
            salvar_log("Arquivo removido", caminho, status="sucesso")
            mostrar_snack("Arquivo removido.", "#2e7d32")
            if dialogo:
                fechar_dialogo(dialogo)
            renderizar_explorador_callback()
        except Exception as ex:
            salvar_log("Erro ao remover arquivo", caminho, status="falha", erro=str(ex))
            mostrar_snack(f"Erro ao remover: {ex}", "#c62828")

    def gerar_pdf_arquivo(caminho):
        try:
            mostrar_snack("Gerando PDF...", "#4dabf7")
            if not caminho.lower().endswith((".doc", ".docx")):
                mostrar_snack("PDF disponível apenas para DOC/DOCX.", "#c62828")
                return

            soffice = localizar_soffice()
            if not soffice:
                mostrar_snack("LibreOffice não encontrado para gerar PDF.", "#c62828")
                return

            pasta_saida = os.path.dirname(caminho)
            processo = subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    pasta_saida,
                    os.path.abspath(caminho),
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if processo.returncode != 0:
                erro = processo.stderr.strip() or processo.stdout.strip()
                raise RuntimeError(erro or "LibreOffice falhou ao converter o arquivo.")

            caminho_pdf = os.path.splitext(caminho)[0] + ".pdf"
            if not os.path.exists(caminho_pdf):
                raise RuntimeError("PDF não foi criado pelo LibreOffice.")
            salvar_log("PDF gerado", caminho_pdf, status="sucesso", caminho_pdf=caminho_pdf)
            mostrar_snack(f"PDF gerado: {caminho_pdf}", "#2e7d32")
            renderizar_explorador_callback()
        except Exception as ex:
            salvar_log("Erro ao gerar PDF", caminho, status="falha", erro=str(ex))
            mostrar_snack(f"Erro ao gerar PDF: {ex}", "#c62828")

    def abrir_dialogo_assinatura(caminho):
        nome_input = ft.TextField(
            label="Nome do assinante",
            value="",
            border_color=theme.BORDER,
            focused_border_color=theme.BLUE,
            color=theme.TEXT_MAIN,
            bgcolor=theme.BG_CARD,
        )
        email_input = ft.TextField(
            label="E-mail do assinante",
            value="",
            border_color=theme.BORDER,
            focused_border_color=theme.BLUE,
            color=theme.TEXT_MAIN,
            bgcolor=theme.BG_CARD,
        )
        status_text = ft.Text("", color=theme.TEXT_MUTED, size=12)

        def enviar(e):
            botao_enviar.disabled = True
            status_text.value = "Enviando documento para assinatura..."
            page.update()

            def executar():
                resultado = assinar_docx_autentique(
                    caminho,
                    nome_input.value or "",
                    email_input.value or "",
                )
                if resultado["success"]:
                    link = ""
                    links = resultado.get("links_assinatura") or []
                    if links:
                        link = links[0].get("link_assinatura") or ""
                    mensagem = resultado["message"]
                    if link:
                        mensagem = f"{mensagem} Link: {link}"
                    salvar_log(
                        "Documento enviado para assinatura",
                        caminho,
                        status="sucesso",
                        caminho_docx=caminho,
                    )
                    mostrar_snack(mensagem, "#2e7d32")
                    fechar_dialogo(dialogo)
                    renderizar_explorador_callback()
                    return

                status_text.value = resultado["message"]
                status_text.color = theme.RED
                botao_enviar.disabled = False
                salvar_log(
                    "Erro ao enviar assinatura",
                    caminho,
                    status="falha",
                    erro=resultado.get("error") or resultado["message"],
                )
                mostrar_snack(resultado["message"], "#c62828")
                page.update()

            page.run_thread(executar)

        botao_enviar = ft.ElevatedButton(
            "Enviar para assinatura",
            on_click=enviar,
            style=ft.ButtonStyle(
                bgcolor={"": theme.BLUE},
                color={"": theme.WHITE},
                shape={"": ft.RoundedRectangleBorder(radius=10)},
            ),
        )
        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_PANEL,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text("Assinar digitalmente", color=theme.TEXT_MAIN, size=16, weight=ft.FontWeight.W_500),
            content=ft.Container(
                width=440,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text(os.path.basename(caminho), color=theme.TEXT_MUTED, size=12),
                        nome_input,
                        email_input,
                        status_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color={"": theme.TEXT_MUTED}),
                    on_click=lambda e: fechar_dialogo(dialogo),
                ),
                botao_enviar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(page, "show_dialog"):
            page.show_dialog(dialogo)
        else:
            page.dialog = dialogo
            dialogo.open = True
            page.update()

    def localizar_soffice():
        candidatos = [
            shutil.which("soffice"),
            shutil.which("soffice.exe"),
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for caminho in candidatos:
            if caminho and os.path.exists(caminho):
                return caminho
        return None

    def listar_resultados_pesquisa(termo):
        resultados = []
        termo = termo.lower()
        if not termo or not os.path.exists(pasta_raiz):
            return resultados

        for raiz, _, arquivos in os.walk(pasta_raiz):
            for arquivo in arquivos:
                if arquivo.startswith("."):
                    continue
                if termo in arquivo.lower():
                    resultados.append(os.path.join(raiz, arquivo))

        return sorted(resultados, key=lambda caminho: os.path.getmtime(caminho), reverse=True)

    partes = ["Contratos"]
    if nivel_atual["ano"]:  partes.append(str(nivel_atual["ano"]))
    if nivel_atual["mes"]:  partes.append(f"{nivel_atual['mes']:02d}")
    if nivel_atual["dia"]:  partes.append(f"{nivel_atual['dia']:02d}")

    def navegar_breadcrumb(indice):
        nivel_atual["pesquisa"] = ""
        if indice == 0:
            nivel_atual.update({"nivel": "raiz", "ano": None, "mes": None, "dia": None})
        elif indice == 1:
            nivel_atual.update({"nivel": "ano", "mes": None, "dia": None})
        elif indice == 2:
            nivel_atual.update({"nivel": "mes", "dia": None})
        elif indice == 3:
            nivel_atual.update({"nivel": "dia"})
        renderizar_explorador_callback()

    breadcrumb_controls = []
    for i, parte in enumerate(partes):
        breadcrumb_controls.append(
            ft.Container(
                ink=True,
                border_radius=8,
                padding=ft.Padding(left=6, right=6, top=4, bottom=4),
                on_click=lambda e, idx=i: navegar_breadcrumb(idx),
                content=ft.Text(
                    parte,
                    color=theme.TEXT_MAIN if i == len(partes)-1 else theme.BLUE,
                    size=13,
                    weight=ft.FontWeight.W_500 if i == len(partes)-1 else ft.FontWeight.W_400,
                ),
            )
        )
        if i < len(partes) - 1:
            breadcrumb_controls.append(
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=theme.TEXT_DIM, size=16)
            )

    breadcrumb = ft.Container(
        bgcolor=theme.BG_CARD,
        border_radius=14,
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        content=ft.Row(controls=breadcrumb_controls, spacing=4)
    )

    campo_pesquisa = ft.TextField(
        value=termo_pesquisa,
        hint_text="Pesquisar contrato por nome",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        bgcolor=theme.BG_CARD,
        border_color=theme.BORDER,
        focused_border_color=theme.BLUE,
        color=theme.TEXT_MAIN,
        hint_style=ft.TextStyle(color=theme.TEXT_MUTED),
        border_radius=12,
        height=44,
        on_submit=pesquisar_contratos,
    )

    btn_pesquisar = ft.IconButton(
        icon=ft.Icons.SEARCH_ROUNDED,
        icon_color=theme.BLUE,
        tooltip="Pesquisar",
        on_click=pesquisar_contratos,
    )

    btn_limpar_pesquisa = ft.IconButton(
        icon=ft.Icons.CLOSE_ROUNDED,
        icon_color=theme.TEXT_MUTED,
        tooltip="Limpar pesquisa",
        on_click=limpar_pesquisa,
        visible=bool(termo_pesquisa),
    )

    btn_atualizar = ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.REFRESH_ROUNDED, color=theme.BLUE, size=18),
            ft.Text("Atualizar", color=theme.TEXT_MAIN, size=13),
        ]),
        on_click=atualizar_explorador,
        style=ft.ButtonStyle(
            bgcolor={"": theme.BG_CARD},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, theme.BORDER)},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )

    if termo_pesquisa:
        resultados = listar_resultados_pesquisa(termo_pesquisa)
        if resultados:
            for caminho_arq in resultados:
                try:
                    arq = os.path.basename(caminho_arq)
                    stat = os.stat(caminho_arq)
                    tam_str = formatar_tamanho_legivel(stat.st_size)
                    hora = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                    rel = os.path.relpath(os.path.dirname(caminho_arq), pasta_raiz)
                    info = f"{tam_str} - {hora} - {rel}"
                except:
                    arq = os.path.basename(caminho_arq)
                    info = "Arquivo"
                lista.controls.append(
                    criar_item_arquivo(
                        arq, info, caminho_arq, abrir_arquivo,
                        confirmar_remocao, gerar_pdf_arquivo, abrir_dialogo_assinatura,
                        status_assinatura_arquivo(caminho_arq),
                    )
                )
        else:
            lista.controls.append(ft.Container(
                alignment=ft.Alignment(0, 0), padding=40,
                content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, color="#555", size=48),
                        ft.Text("Nenhum contrato encontrado.", color="#555", size=14),
                    ])
            ))

    elif nivel == "raiz":
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
                    criar_item_pasta(ano, ft.Icons.FOLDER_ROUNDED, theme.BLUE,
                               abrir_ano, f"{qtd} arquivo(s)"))
        if not lista.controls:
            lista.controls.append(ft.Container(
                alignment=ft.Alignment(0, 0), padding=40,
                content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OFF_ROUNDED, color=theme.TEXT_MUTED, size=48),
                        ft.Text("Nenhum contrato ainda.", color=theme.TEXT_MUTED, size=14),
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
                    criar_item_pasta(f"{mes} — {nm}", ft.Icons.CALENDAR_MONTH_ROUNDED, theme.BLUE,
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
                    criar_item_pasta(f"Dia {dia}{label}", ft.Icons.TODAY_ROUNDED, theme.BLUE,
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
                    lista.controls.append(
                        criar_item_arquivo(
                            arq, info, caminho_arq, abrir_arquivo,
                            confirmar_remocao, gerar_pdf_arquivo, abrir_dialogo_assinatura,
                            status_assinatura_arquivo(caminho_arq),
                        )
                    )
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
            ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, color=theme.WHITE, size=18),
            ft.Text("Importar arquivo", color="white", size=13),
        ]),
        on_click=importar_arquivo,
        style=ft.ButtonStyle(
            bgcolor={"": theme.BLUE},
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
                ft.Row(spacing=10, controls=[btn_atualizar, btn_importar]),
            ]
        ),
        ft.Row(
            spacing=10,
            controls=[
                ft.Container(expand=True, content=campo_pesquisa),
                btn_pesquisar,
                btn_limpar_pesquisa,
            ]
        ),
        ft.Container(height=6),
        ft.Container(expand=True, content=lista),
    ]
    page.update()
