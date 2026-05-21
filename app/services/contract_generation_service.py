import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


def gerar_contrato_por_reserva(reserva_id: str, reserva_data: dict) -> dict:
    try:
        reserva_id = str(reserva_id or "").strip()

        if not reserva_id:
            return _resultado(
                success=False,
                status="falha",
                message="ID da reserva não informado.",
                id_reserva=reserva_id,
                error="ID da reserva vazio.",
            )

        if not isinstance(reserva_data, dict) or not reserva_data:
            return _resultado(
                success=False,
                status="falha",
                message="Dados da reserva não encontrados.",
                id_reserva=reserva_id,
                error="JSON da reserva vazio ou inválido.",
            )

        tipovenda = _buscar_valor(reserva_data, "tipovenda")
        tipo_contrato = _identificar_tipo_contrato(tipovenda)
        tipo_comprador = _identificar_tipo_comprador(reserva_data)
        modelo = f"{tipo_contrato}_{tipo_comprador}"

        geracao = _gerar_docx_contrato(reserva_id, reserva_data, modelo)
        if not geracao["success"]:
            return _resultado(
                success=False,
                status="falha",
                message=geracao["message"],
                id_reserva=reserva_id,
                modelo=modelo,
                error=geracao["error"],
            )

        return _resultado(
            success=True,
            status="sucesso",
            message="Contrato gerado com sucesso.",
            id_reserva=reserva_id,
            modelo=modelo,
            caminho_docx=geracao["caminho_docx"],
        )

    except Exception as erro:
        return _resultado(
            success=False,
            status="falha",
            message="Falha ao preparar geração do contrato.",
            id_reserva=str(reserva_id or "").strip(),
            error=str(erro),
        )


def _resultado(success, status, message, id_reserva, modelo=None,
               caminho_docx=None, caminho_pdf=None, error=None):
    return {
        "success": success,
        "status": status,
        "message": message,
        "id_reserva": id_reserva,
        "modelo": modelo,
        "caminho_docx": caminho_docx,
        "caminho_pdf": caminho_pdf,
        "error": error,
    }


def _gerar_docx_contrato(reserva_id, reserva_data, modelo):
    template_path = _template_por_modelo(modelo)

    if template_path is None:
        return {
            "success": False,
            "message": f"Template não encontrado para o modelo {modelo}.",
            "caminho_docx": None,
            "error": "Template de contrato não disponível.",
        }

    try:
        dados = _normalizar_dados_contrato(reserva_data)
        pasta_saida = _backend_path() / "output"
        caminho_docx = pasta_saida / f"contrato_reserva_{reserva_id}.docx"
        _gerar_docx_por_template(template_path, caminho_docx, dados)

        return {
            "success": True,
            "message": "Contrato DOCX gerado.",
            "caminho_docx": str(caminho_docx),
            "error": None,
        }
    except Exception as erro:
        return {
            "success": False,
            "message": "Falha ao gerar arquivo DOCX do contrato.",
            "caminho_docx": None,
            "error": str(erro),
        }


def _template_por_modelo(modelo):
    templates = {
        "financiamento_comprador_unico": "contrato_financiamento_comprador_unico.docx",
        "investimento_comprador_unico": "contrato_financiamento_comprador_unico.docx",
    }
    nome_template = templates.get(modelo)
    if not nome_template:
        return None

    template_path = _backend_path() / "template_contrato" / nome_template
    if not template_path.exists():
        return None

    return template_path


def _normalizar_dados_contrato(reserva_data):
    backend_path = _backend_path()
    backend_parent = str(backend_path.parent)

    if backend_parent not in sys.path:
        sys.path.insert(0, backend_parent)

    from backend import normalizar_dados

    normalizar_dados.re = re
    normalizar_dados.datetime = datetime

    return normalizar_dados.normalizar_dados_cvcrm(reserva_data)


def _gerar_docx_por_template(template_path, output_path, variaveis):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(template_path, "r") as origem:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as destino:
            for item in origem.infolist():
                conteudo = origem.read(item.filename)

                if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                    texto = conteudo.decode("utf-8")
                    for marcador, valor in variaveis.items():
                        texto = texto.replace(marcador, escape(str(valor)))
                    conteudo = texto.encode("utf-8")

                destino.writestr(item, conteudo)


def _backend_path():
    return Path(__file__).resolve().parents[3] / "backend"


def _buscar_valor(data, chave):
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).lower() == chave.lower():
                return value
            if isinstance(value, (dict, list)):
                encontrado = _buscar_valor(value, chave)
                if encontrado is not None:
                    return encontrado

    if isinstance(data, list):
        for item in data:
            encontrado = _buscar_valor(item, chave)
            if encontrado is not None:
                return encontrado

    return None


def _identificar_tipo_contrato(tipovenda):
    valor = _normalizar_texto(tipovenda)

    if "financi" in valor:
        return "financiamento"

    if "invest" in valor:
        return "investimento"

    return "investimento"


def _identificar_tipo_comprador(reserva_data):
    compradores = (
        _buscar_valor(reserva_data, "compradores")
        or _buscar_valor(reserva_data, "clientes")
        or _buscar_valor(reserva_data, "cliente")
    )

    if isinstance(compradores, list) and len(compradores) > 1:
        return "multiplos_compradores"

    return "comprador_unico"


def _normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip().lower()
