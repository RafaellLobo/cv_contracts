import datetime
import json
import os

from app.config.settings import LOG_FILE


def salvar_log(acao, detalhe="", id_reserva=None, modelo=None,
               status=None, caminho_docx=None, caminho_pdf=None, erro=None):
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            logs = []

    entrada = {
        "timestamp":    datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "acao":         acao,
        "detalhe":      detalhe,
        "id_reserva":   id_reserva or "",
        "modelo":       modelo or "",
        "status":       status or "",
        "caminho_docx": caminho_docx or "",
        "caminho_pdf":  caminho_pdf or "",
        "erro":         erro or "",
    }

    logs.insert(0, entrada)
    logs = logs[:200]
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except:
        pass


def carregar_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []
