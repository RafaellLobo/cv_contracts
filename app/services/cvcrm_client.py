import json
import threading
import urllib.error
import urllib.request

from app.config.settings import CV_BASE_URL, CV_EMAIL, CV_TOKEN


def consultar_reserva(reserva_id, callback):
    def _request():
        url = f"https://prati.cvcrm.com.br/{CV_BASE_URL}/api/v1/comercial/reservas/{reserva_id}"
        headers = {
            "accept":       "application/json",
            "Content-Type": "application/json",
            "email":        CV_EMAIL,
            "token":        CV_TOKEN,
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                callback(data, None)
        except urllib.error.HTTPError as e:
            callback(None, f"Erro HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            callback(None, f"Erro de conexão: {e.reason}")
        except Exception as e:
            callback(None, str(e))
    threading.Thread(target=_request, daemon=True).start()
