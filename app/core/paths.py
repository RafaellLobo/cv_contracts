import datetime
import os

from app.config.settings import PASTA_RAIZ


def caminho_por_data(data):
    return os.path.join(
        PASTA_RAIZ,
        str(data.year),
        f"{data.month:02d}",
        f"{data.day:02d}"
    )


def garantir_estrutura_hoje():
    hoje = datetime.date.today()
    caminho = caminho_por_data(hoje)
    os.makedirs(caminho, exist_ok=True)
    return caminho
