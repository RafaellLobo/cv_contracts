import datetime

import flet as ft


def create_calendar_controls(page, hoje, data_selecionada, mes_calendario,
                             renderizar_explorador):
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

    def fechar_calendario():
        calendario_container.visible = False
        overlay_calendario.visible = False
        page.update()

    overlay_calendario = ft.Container(
        visible=False,
        width=1400, height=800,
        bgcolor="#00000001",
        on_click=lambda e: fechar_calendario(),
    )

    def construir_calendario():
        ano = mes_calendario["ano"]
        mes = mes_calendario["mes"]
        nomes = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        nome_mes = nomes[mes]

        primeiro_dia = datetime.date(ano, mes, 1)
        dia_semana_ini = primeiro_dia.weekday()
        ultimo_dia = (datetime.date(ano, mes % 12 + 1, 1) if mes < 12
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
            data_dia = datetime.date(ano, mes, dia)
            cor_bg = "#4dabf7" if data_dia == data_selecionada["data"] else (
                     "#1a3a5c" if data_dia == hoje else "transparent")
            cor_txt = "white" if (data_dia == data_selecionada["data"] or data_dia == hoje) else "#e0e0e0"
            peso = ft.FontWeight.BOLD if (data_dia == hoje or data_dia == data_selecionada["data"]) else ft.FontWeight.NORMAL

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
        overlay_calendario.visible = True
        page.update()

    return {
        "badge_data": badge_data,
        "calendario_container": calendario_container,
        "overlay_calendario": overlay_calendario,
        "construir_calendario": construir_calendario,
        "navegar_mes": navegar_mes,
        "selecionar_data": selecionar_data,
        "limpar_data": limpar_data,
        "abrir_calendario": abrir_calendario,
        "fechar_calendario": fechar_calendario,
    }
