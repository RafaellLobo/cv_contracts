import os

from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"), encoding="utf-8-sig")

CV_BASE_URL = os.getenv("CV_BASE_URL", "")
CV_EMAIL = os.getenv("CV_EMAIL", "")
CV_TOKEN = os.getenv("CV_TOKEN", "")
AUTENTIQUE_TOKEN = os.getenv("AUTENTIQUE_TOKEN", "")
AUTENTIQUE_SANDBOX = os.getenv("AUTENTIQUE_SANDBOX", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "sim",
}

PASTA_RAIZ = os.path.join(os.path.expanduser("~"), "Contratos")
LOG_FILE = os.path.join(PASTA_RAIZ, ".logs.json")
AUTENTIQUE_DOCUMENTS_FILE = os.path.join(PASTA_RAIZ, ".documentos_autentique.json")
