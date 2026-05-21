import flet as ft
import os
import datetime
from pathlib import Path


from app.config.settings import CV_BASE_URL, CV_EMAIL, CV_TOKEN, PASTA_RAIZ
from app.core.paths import garantir_estrutura_hoje
from app.repositories.log_repository import carregar_logs, salvar_log
from app.services.cvcrm_client import consultar_reserva
from app.services.file_service import abrir_arquivo_sistema, formatar_tamanho_legivel, listar_itens_visiveis
from app.services.report_service import gerar_relatorio_pdf_do_dia


def main(page: ft.Page):

    page.title        = "CV Contracts"
    page.window_width  = 1400
    page.window_height = 800
    page.theme_mode   = ft.ThemeMode.DARK
    page.padding      = 0
    page.bgcolor      = "#18191A"

    garantir_estrutura_hoje()
    salvar_log("App iniciado")

    hoje = datetime.date.today()
    data_selecionada  = {"data": None}
    mes_calendario    = {"ano": hoje.year, "mes": hoje.month}
    nivel_atual       = {"nivel": "raiz", "ano": None, "mes": None, "dia": None}

    def mostrar_snack(mensagem, cor="#4dabf7"):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensagem, color="white"),
            bgcolor=cor,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    # =====================================================
    # MODAL — GERAR NOVO CONTRATO
    # =====================================================

    def abrir_modal_novo_contrato(e=None):
        campo_id    = ft.TextField(
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
        loading     = ft.ProgressRing(width=20, height=20, color="#4dabf7", visible=False)
        btn_gerar   = ft.ElevatedButton(
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
            dialogo.open = False
            page.update()

        def on_resultado(data, erro):
            loading.visible = False
            btn_gerar.disabled = False
            if erro:
                status_text.value = f"❌ {erro}"
                status_text.color = "#f87171"
                salvar_log("Erro ao consultar reserva",
                           id_reserva=campo_id.value.strip(),
                           status="falha", erro=erro)
            else:
                status_text.value = "✓ Reserva encontrada! Gerando contrato..."
                status_text.color = "#34d399"
                salvar_log("Reserva consultada",
                           id_reserva=campo_id.value.strip(),
                           status="sucesso",
                           detalhe=str(data)[:120])
                # Aqui entrará a lógica de escolha de template e geração do contrato
            page.update()

        def on_gerar(e):
            reserva_id = campo_id.value.strip()
            if not reserva_id:
                status_text.value = "⚠ Informe o ID da reserva."
                status_text.color = "#f59e0b"
                page.update()
                return
            if not CV_EMAIL or not CV_TOKEN or not CV_BASE_URL:
                status_text.value = "⚠ Configure o .env com CV_BASE_URL, CV_EMAIL e CV_TOKEN."
                status_text.color = "#f59e0b"
                page.update()
                return
            loading.visible    = True
            btn_gerar.disabled = True
            status_text.value  = "Consultando API..."
            status_text.color  = "#B0B3B8"
            page.update()
            consultar_reserva(reserva_id, on_resultado)

        btn_gerar.on_click   = on_gerar
        btn_cancelar.on_click = fechar

        page.dialog = dialogo
        dialogo.open = True
        page.update()

    titulo_pagina = ft.Text("Contratos", size=26, weight=ft.FontWeight.BOLD, color="white")
    subtitulo     = ft.Text("Visão geral do sistema", color="#B0B3B8", size=13)

    badge_data = ft.Container(
        visible=False,
        bgcolor="#1a3a5c",
        border_radius=20,
        padding=ft.Padding(left=12, right=12, top=6, bottom=6),
        content=ft.Row(
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.CALENDAR_TODAY, color="#4dabf7", size=14),
                ft.Text("", color="#4dabf7", size=12, weight=ft.FontWeight.W_500),
            ]
        )
    )

    area_conteudo = ft.Column(expand=True, spacing=0)

    calendario_container = ft.Container(
        visible=False,
        bgcolor="#1e2023",
        border_radius=16,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=30, color="#00000066", offset=ft.Offset(0, 8)),
        border=ft.Border(
            top=ft.BorderSide(1, "#2d2f33"), bottom=ft.BorderSide(1, "#2d2f33"),
            left=ft.BorderSide(1, "#2d2f33"), right=ft.BorderSide(1, "#2d2f33")
        ),
        width=300,
    )

    overlay_calendario = ft.Container(
        visible=False,
        width=1400, height=800,
        bgcolor="#00000001",
        on_click=lambda e: fechar_calendario(),
    )

    def construir_calendario():
        ano      = mes_calendario["ano"]
        mes      = mes_calendario["mes"]
        nomes    = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        nome_mes = nomes[mes]

        primeiro_dia    = datetime.date(ano, mes, 1)
        dia_semana_ini  = primeiro_dia.weekday()
        ultimo_dia      = (datetime.date(ano, mes % 12 + 1, 1) if mes < 12
                           else datetime.date(ano + 1, 1, 1)) - datetime.timedelta(days=1)

        cabecalho_dias = ft.Row(
            spacing=2,
            controls=[
                ft.Container(width=34, height=28, alignment=ft.Alignment(0,0),
                    content=ft.Text(d, size=11, color="#B0B3B8", weight=ft.FontWeight.W_600))
                for d in ["S","T","Q","Q","S","S","D"]
            ]
        )

        semanas, semana = [], []
        for _ in range(dia_semana_ini):
            semana.append(ft.Container(width=34, height=34))

        for dia in range(1, ultimo_dia.day + 1):
            data_dia   = datetime.date(ano, mes, dia)
            cor_bg     = "#4dabf7" if data_dia == data_selecionada["data"] else (
                         "#1a3a5c" if data_dia == hoje else "transparent")
            cor_txt    = "white" if (data_dia == data_selecionada["data"] or data_dia == hoje) else "#e0e0e0"
            peso       = ft.FontWeight.BOLD if (data_dia == hoje or data_dia == data_selecionada["data"]) else ft.FontWeight.NORMAL

            semana.append(ft.Container(
                width=34, height=34, bgcolor=cor_bg, border_radius=8,
                alignment=ft.Alignment(0,0), ink=True,
                on_click=lambda e, dt=data_dia: selecionar_data(dt),
                content=ft.Text(str(dia), size=13, color=cor_txt, weight=peso)
            ))
            if len(semana) == 7:
                semanas.append(ft.Row(controls=semana, spacing=2))
                semana = []

        if semana:
            while len(semana) < 7:
                semana.append(ft.Container(width=34, height=34))
            semanas.append(ft.Row(controls=semana, spacing=2))

        calendario_container.content = ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(icon=ft.Icons.CHEVRON_LEFT_ROUNDED, icon_color="white",
                            icon_size=20, on_click=lambda e: navegar_mes(-1),
                            style=ft.ButtonStyle(bgcolor={"": "#2d2f33"},
                                shape={"": ft.RoundedRectangleBorder(radius=8)})),
                        ft.Text(f"{nome_mes} {ano}", color="white", size=14, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_color="white",
                            icon_size=20, on_click=lambda e: navegar_mes(1),
                            style=ft.ButtonStyle(bgcolor={"": "#2d2f33"},
                                shape={"": ft.RoundedRectangleBorder(radius=8)})),
                    ]
                ),
                cabecalho_dias,
                ft.Divider(color="#2d2f33", height=1),
                ft.Column(controls=semanas, spacing=2),
                ft.Divider(color="#2d2f33", height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.TextButton("Limpar", on_click=lambda e: limpar_data(),
                            style=ft.ButtonStyle(color="#B0B3B8")),
                        ft.TextButton("Hoje", on_click=lambda e: selecionar_data(hoje),
                            style=ft.ButtonStyle(color="#4dabf7")),
                    ]
                )
            ]
        )
        page.update()

    def navegar_mes(delta):
        mes = mes_calendario["mes"] + delta
        ano = mes_calendario["ano"]
        if mes > 12: mes, ano = 1, ano + 1
        elif mes < 1: mes, ano = 12, ano - 1
        mes_calendario["mes"] = mes
        mes_calendario["ano"] = ano
        construir_calendario()

    def selecionar_data(data):
        data_selecionada["data"] = data
        badge_data.visible = True
        badge_data.content.controls[1].value = data.strftime("%d/%m/%Y")
        fechar_calendario()
        renderizar_explorador()

    def limpar_data():
        data_selecionada["data"] = None
        badge_data.visible = False
        fechar_calendario()
        renderizar_explorador()

    def abrir_calendario(e):
        construir_calendario()
        calendario_container.visible = True
        overlay_calendario.visible   = True
        page.update()

    def fechar_calendario():
        calendario_container.visible = False
        overlay_calendario.visible   = False
        page.update()

    def gerar_pdf_do_dia(e):
        try:
            resultado = gerar_relatorio_pdf_do_dia(data_selecionada["data"] or hoje)
            caminho_pdf = resultado["path"]
            salvar_log("PDF gerado", caminho_pdf,
                       status="sucesso", caminho_pdf=caminho_pdf)
            mostrar_snack(f"✓ PDF salvo em: {caminho_pdf}", "#2e7d32")

        except ImportError:
            mostrar_snack("❌ Instale reportlab: pip install reportlab", "#c62828")
        except Exception as ex:
            mostrar_snack(f"❌ Erro: {ex}", "#c62828")

    def renderizar_dashboard():
        titulo_pagina.value = "Dashboard"
        subtitulo.value     = "Visão geral do sistema"

        total_anos    = 0
        total_meses   = 0
        total_dias    = 0
        total_arquivos = 0
        arquivos_hoje  = 0
        caminho_hoje   = os.path.join(PASTA_RAIZ, str(hoje.year),
                                      f"{hoje.month:02d}", f"{hoje.day:02d}")

        if os.path.exists(PASTA_RAIZ):
            for ano in os.listdir(PASTA_RAIZ):
                p_ano = os.path.join(PASTA_RAIZ, ano)
                if not os.path.isdir(p_ano) or not ano.isdigit(): continue
                total_anos += 1
                for mes in os.listdir(p_ano):
                    p_mes = os.path.join(p_ano, mes)
                    if not os.path.isdir(p_mes): continue
                    total_meses += 1
                    for dia in os.listdir(p_mes):
                        p_dia = os.path.join(p_mes, dia)
                        if not os.path.isdir(p_dia): continue
                        total_dias += 1
                        for arq in os.listdir(p_dia):
                            if not arq.startswith('.'):
                                total_arquivos += 1

        if os.path.exists(caminho_hoje):
            arquivos_hoje = len([a for a in os.listdir(caminho_hoje)
                                  if not a.startswith('.')])

        def card_stat(icone, cor, valor, label):
            return ft.Container(
                expand=True,
                bgcolor="#242526",
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
                        ft.Text(str(valor), size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(label, size=12, color="#B0B3B8"),
                    ]
                )
            )

        logs = carregar_logs()[:5]
        itens_log = []
        for log in logs:
            itens_log.append(
                ft.Container(
                    bgcolor="#1e1f21",
                    border_radius=10,
                    padding=12,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CIRCLE, color="#4dabf7", size=8),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(log.get("acao",""), color="white", size=13),
                                    ft.Text(log.get("detalhe","")[:60] if log.get("detalhe") else "",
                                        color="#666", size=11),
                                ]
                            ),
                            ft.Text(log.get("timestamp",""), color="#555", size=11),
                        ],
                        spacing=12,
                    )
                )
            )

        if not itens_log:
            itens_log.append(ft.Text("Nenhuma atividade ainda.", color="#555", size=13))

        area_conteudo.controls = [
            ft.Row(
                spacing=14,
                controls=[
                    card_stat(ft.Icons.FOLDER_ROUNDED,           "#4dabf7", total_anos,     "Anos"),
                    card_stat(ft.Icons.CALENDAR_MONTH_ROUNDED,   "#a78bfa", total_meses,    "Meses"),
                    card_stat(ft.Icons.TODAY_ROUNDED,            "#34d399", total_dias,     "Dias"),
                    card_stat(ft.Icons.DESCRIPTION_ROUNDED,      "#f59e0b", total_arquivos, "Contratos total"),
                    card_stat(ft.Icons.STAR_ROUNDED,             "#fb7185", arquivos_hoje,  "Hoje"),
                ]
            ),
            ft.Container(height=10),
            ft.Text("Atividade Recente", size=16, weight=ft.FontWeight.BOLD, color="white"),
            ft.Container(height=4),
            ft.Column(controls=itens_log, spacing=6),
        ]
        page.update()

    def renderizar_explorador():
        titulo_pagina.value = "Explorador"
        subtitulo.value     = "Contratos organizados por data"
        nivel = nivel_atual["nivel"]

        lista = ft.ListView(expand=True, spacing=6, auto_scroll=False)

        def importar_arquivo(e):
            def on_result(result: ft.FilePickerResultEvent):
                if not result.files:
                    return
                pasta_destino = os.path.join(
                    PASTA_RAIZ, str(hoje.year),
                    f"{hoje.month:02d}", f"{hoje.day:02d}"
                )
                os.makedirs(pasta_destino, exist_ok=True)
                importados = 0
                for f in result.files:
                    try:
                        import shutil
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
                renderizar_explorador()

            picker = ft.FilePicker(on_result=on_result)
            page.overlay.append(picker)
            page.update()
            picker.pick_files(allow_multiple=True)

        def item_pasta(nome, icone, cor, on_click_fn, subtexto=""):
            return ft.Container(
                bgcolor="#242526",
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
                    title=ft.Text(nome, color="white", size=14, weight=ft.FontWeight.W_500),
                    subtitle=ft.Text(subtexto, color="#B0B3B8", size=12) if subtexto else None,
                )
            )

        def item_voltar(fn):
            return ft.Container(
                bgcolor="#242526",
                border_radius=12,
                padding=4,
                ink=True,
                on_click=fn,
                content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, color="#4dabf7"),
                    title=ft.Text("Voltar", color="white"),
                )
            )

        def abrir_arquivo(caminho):
            try:
                abrir_arquivo_sistema(caminho)
                salvar_log("Arquivo aberto", caminho, status="sucesso")
            except Exception as ex:
                mostrar_snack(f"❌ Não foi possível abrir: {ex}", "#c62828")

        def item_arquivo(nome, info, caminho_completo):
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
                bgcolor="#242526",
                border_radius=14,
                padding=10,
                ink=True,
                on_click=lambda e, c=caminho_completo: abrir_arquivo(c),
                content=ft.ListTile(
                    leading=ft.Container(
                        width=42, height=42,
                        bgcolor=cor + "22",
                        border_radius=10,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icone, color=cor, size=22)
                    ),
                    title=ft.Text(nome, color="white", size=14, weight=ft.FontWeight.W_500),
                    subtitle=ft.Text(info, color="#B0B3B8", size=11),
                    trailing=ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, color="#555", size=16),
                )
            )

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
            if os.path.exists(PASTA_RAIZ):
                anos = sorted([a for a in os.listdir(PASTA_RAIZ)
                                if os.path.isdir(os.path.join(PASTA_RAIZ, a)) and a.isdigit()],
                               reverse=True)
                for ano in anos:
                    p = os.path.join(PASTA_RAIZ, ano)
                    qtd = sum(len(os.listdir(os.path.join(p, m, d)))
                              for m in os.listdir(p) if os.path.isdir(os.path.join(p, m))
                              for d in os.listdir(os.path.join(p, m)) if os.path.isdir(os.path.join(p, m, d)))
                    def abrir_ano(e, a=int(ano)):
                        nivel_atual.update({"nivel":"ano","ano":a,"mes":None,"dia":None})
                        renderizar_explorador()
                    lista.controls.append(
                        item_pasta(ano, ft.Icons.FOLDER_ROUNDED, "#4dabf7",
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
            lista.controls.append(item_voltar(lambda e: (
                nivel_atual.update({"nivel":"raiz","ano":None,"mes":None,"dia":None}),
                renderizar_explorador()
            )))
            p_ano = os.path.join(PASTA_RAIZ, str(nivel_atual["ano"]))
            meses_nomes = ["","Jan","Fev","Mar","Abr","Mai","Jun",
                           "Jul","Ago","Set","Out","Nov","Dez"]
            if os.path.exists(p_ano):
                meses = sorted([m for m in os.listdir(p_ano)
                                 if os.path.isdir(os.path.join(p_ano, m)) and m.isdigit()])
                for mes in meses:
                    p_mes = os.path.join(p_ano, mes)
                    qtd   = sum(len(os.listdir(os.path.join(p_mes, d)))
                                for d in os.listdir(p_mes)
                                if os.path.isdir(os.path.join(p_mes, d)))
                    nm    = meses_nomes[int(mes)] if int(mes) <= 12 else mes
                    def abrir_mes(e, m=int(mes)):
                        nivel_atual.update({"nivel":"mes","mes":m,"dia":None})
                        renderizar_explorador()
                    lista.controls.append(
                        item_pasta(f"{mes} — {nm}", ft.Icons.CALENDAR_MONTH_ROUNDED, "#a78bfa",
                                   abrir_mes, f"{qtd} arquivo(s)"))

        elif nivel == "mes":
            lista.controls.append(item_voltar(lambda e: (
                nivel_atual.update({"nivel":"ano","mes":None,"dia":None}),
                renderizar_explorador()
            )))
            p_mes = os.path.join(PASTA_RAIZ, str(nivel_atual["ano"]),
                                  f"{nivel_atual['mes']:02d}")
            if os.path.exists(p_mes):
                dias = sorted([d for d in os.listdir(p_mes)
                                if os.path.isdir(os.path.join(p_mes, d)) and d.isdigit()])
                for dia in dias:
                    p_dia = os.path.join(p_mes, dia)
                    qtd   = len([a for a in os.listdir(p_dia) if not a.startswith('.')])
                    data_dia = datetime.date(nivel_atual["ano"], nivel_atual["mes"], int(dia))
                    label = " — Hoje" if data_dia == hoje else ""
                    def abrir_dia(e, d=int(dia)):
                        nivel_atual.update({"nivel":"dia","dia":d})
                        renderizar_explorador()
                    lista.controls.append(
                        item_pasta(f"Dia {dia}{label}", ft.Icons.TODAY_ROUNDED, "#34d399",
                                   abrir_dia, f"{qtd} arquivo(s)"))

        elif nivel == "dia":
            lista.controls.append(item_voltar(lambda e: (
                nivel_atual.update({"nivel":"mes","dia":None}),
                renderizar_explorador()
            )))
            p_dia = os.path.join(PASTA_RAIZ, str(nivel_atual["ano"]),
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
                            stat    = os.stat(caminho_arq)
                            tam_str = formatar_tamanho_legivel(stat.st_size)
                            hora = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                            info = f"{tam_str} • {hora}"
                        except:
                            caminho_arq = os.path.join(p_dia, arq)
                            info = "Arquivo"
                        lista.controls.append(item_arquivo(arq, info, caminho_arq))
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

    def renderizar_logs():
        titulo_pagina.value = "Logs"
        subtitulo.value     = "Histórico de atividades"

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

        def badge(texto, cor):
            return ft.Container(
                bgcolor=cor + "22",
                border_radius=6,
                padding=ft.Padding(left=8, right=8, top=3, bottom=3),
                content=ft.Text(texto, color=cor, size=10, weight=ft.FontWeight.W_500)
            )

        itens = []
        for log in logs:
            cor   = cor_status(log)
            icone = icone_status(log)

            badges = []
            if log.get("id_reserva"):
                badges.append(badge(f"Reserva #{log['id_reserva']}", "#4dabf7"))
            if log.get("modelo"):
                badges.append(badge(log["modelo"], "#a78bfa"))
            if log.get("status"):
                cores_status = {"sucesso": "#34d399", "ignorado": "#f59e0b",
                                "pendente": "#a78bfa", "falha": "#f87171"}
                badges.append(badge(log["status"].upper(),
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

    def trocar_pagina(nome):
        if   nome == "Dashboard":  renderizar_dashboard()
        elif nome == "Explorador": renderizar_explorador()
        elif nome == "Logs":       renderizar_logs()

    # =====================================================
    # SIDEBAR — sem Assinar e sem Configurações
    # =====================================================

    itens_sidebar = [
        (ft.Icons.DASHBOARD_ROUNDED,    "Dashboard"),
        (ft.Icons.FOLDER_ROUNDED,       "Explorador"),
        (ft.Icons.RECEIPT_LONG_ROUNDED, "Logs"),
    ]

    def item_sidebar(icone, texto):
        return ft.Container(
            border_radius=12, ink=True,
            padding=ft.Padding(left=14, right=14, top=11, bottom=11),
            on_click=lambda e, t=texto: trocar_pagina(t),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icone, color="#B0B3B8", size=20),
                    ft.Text(texto, color="#e0e0e0", size=14)
                ]
            )
        )

    sidebar = ft.Container(
        width=250,
        bgcolor="#111315",
        padding=ft.Padding(left=16, right=16, top=24, bottom=24),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Container(
                    padding=ft.Padding(left=4, right=0, top=0, bottom=4),
                    content=ft.Column(spacing=2, controls=[
                        ft.Text("CV Contracts", size=22, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Automação Jurídica", color="#555", size=12),
                    ])
                ),
                ft.Divider(color="#2d2f33", height=20),
                *[item_sidebar(ic, txt) for ic, txt in itens_sidebar],
            ]
        )
    )

    btn_novo_contrato = ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.ADD_ROUNDED, color="white", size=18),
            ft.Text("Gerar novo contrato", color="white", size=13, weight=ft.FontWeight.W_500),
        ]),
        on_click=abrir_modal_novo_contrato,
        style=ft.ButtonStyle(
            bgcolor={"": "#4dabf7"},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )

    btn_calendario = ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color="#4dabf7", size=18),
            ft.Text("Calendário", color="white", size=13),
        ]),
        on_click=abrir_calendario,
        style=ft.ButtonStyle(
            bgcolor={"": "#242526"},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, "#2d2f33")},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )

    btn_pdf = ft.ElevatedButton(
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color="#66bb6a", size=18),
            ft.Text("Gerar PDF do Dia", color="#66bb6a", size=13, weight=ft.FontWeight.W_500),
        ]),
        on_click=gerar_pdf_do_dia,
        style=ft.ButtonStyle(
            bgcolor={"": "#1a3a1a"},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            side={"": ft.BorderSide(1, "#2e5c2e")},
            padding={"": ft.Padding(left=14, right=14, top=10, bottom=10)},
        )
    )

    conteudo = ft.Container(
        expand=True,
        padding=28,
        content=ft.Column(
            expand=True, spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(spacing=2, controls=[titulo_pagina, subtitulo]),
                        ft.Row(spacing=10, controls=[badge_data, btn_calendario, btn_pdf, btn_novo_contrato])
                    ]
                ),
                ft.Divider(color="#2d2f33", height=1),
                ft.Container(expand=True, content=area_conteudo),
            ]
        )
    )

    stack_principal = ft.Stack(
        expand=True,
        controls=[
            ft.Row(controls=[sidebar, conteudo], expand=True),
            overlay_calendario,
            ft.Container(content=calendario_container, right=30, top=90, visible=True),
        ]
    )

    page.add(stack_principal)
    renderizar_dashboard()


ft.app(target=main)
