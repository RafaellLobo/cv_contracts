import os

import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class CVCRMClient:
    def __init__(self):
        self.base_url = os.getenv("CVCRM_BASE_URL") or os.getenv("CV_BASE_URL")
        self.email = os.getenv("CVCRM_EMAIL") or os.getenv("CV_EMAIL")
        self.token = os.getenv("CVCRM_TOKEN") or os.getenv("CV_TOKEN")

        if not self.base_url or not self.email or not self.token:
            raise ValueError("Verifique URL, Email ou Token no .env")

    def _headers(self):
        return{
            "accept": "application/json",
            "Content-Type": "application/json",
            "email": self.email,
            "token": self.token,
        }

    def buscar_reserva(self, reserva_id):
        url = f"{self.base_url}/api/v1/comercial/reservas/{reserva_id}"
        response = requests.get(url, headers=self._headers(), timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Erro ao buscar reserva: {response.status_code} - {response.text}"
            )
        return response.json()
