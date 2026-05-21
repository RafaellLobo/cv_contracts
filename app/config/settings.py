import os

from dotenv import load_dotenv


load_dotenv()

CV_BASE_URL = os.getenv("CV_BASE_URL", "")
CV_EMAIL = os.getenv("CV_EMAIL", "")
CV_TOKEN = os.getenv("CV_TOKEN", "")

PASTA_RAIZ = os.path.join(os.path.expanduser("~"), "Contratos")
LOG_FILE = os.path.join(PASTA_RAIZ, ".logs.json")
