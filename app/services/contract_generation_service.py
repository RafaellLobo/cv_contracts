import copy
import re
import sys
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from app.core.paths import garantir_estrutura_hoje


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("w", W_NS)


TEMPLATE_MODELOS = {
    "financiamento_comprador_unico": [
        "contrato_financiamento_comprador_unico.docx",
        "Desafio 1- financiamento - comprador unico.docx",
    ],
    "financiamento_compradores": [
        "contrato_financiamento_compradores.docx",
        "Desafio 1- financiamento - compradores.docx",
    ],
    "investimento_comprador_unico": [
        "contrato_investimento_comprador_unico.docx",
        "Desafio 1- Investimento - comprador unico.docx",
    ],
    "investimento_compradores": [
        "contrato_investimento_compradores.docx",
        "Desafio 1- Investimento - compradores.docx",
    ],
}


def gerar_contrato_por_reserva(reserva_id: str, reserva_data: dict,
                               dados_contrato: dict | None = None) -> dict:
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

        geracao = _gerar_docx_contrato(reserva_id, reserva_data, modelo, dados_contrato)
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


def preparar_campos_contrato(reserva_data: dict) -> dict:
    try:
        if not isinstance(reserva_data, dict) or not reserva_data:
            return {
                "success": False,
                "message": "Dados da reserva não encontrados.",
                "dados": {},
                "campos": [],
                "error": "JSON da reserva vazio ou inválido.",
            }

        dados = _normalizar_dados_contrato(reserva_data)
        campos = []

        for marcador, valor in dados.items():
            texto = str(valor or "")
            campos.append({
                "marcador": marcador,
                "label": _label_campo(marcador),
                "value": "" if _valor_pendente(texto) else texto,
                "original": texto,
                "missing": _valor_pendente(texto),
            })

        campos.sort(key=lambda campo: (not campo["missing"], campo["label"]))

        return {
            "success": True,
            "message": "Campos preparados.",
            "dados": dados,
            "campos": campos,
            "error": None,
        }
    except Exception as erro:
        return {
            "success": False,
            "message": "Falha ao preparar campos do contrato.",
            "dados": {},
            "campos": [],
            "error": str(erro),
        }


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


def _gerar_docx_contrato(reserva_id, reserva_data, modelo, dados_contrato=None):
    template_path = _template_por_modelo(modelo)

    if template_path is None:
        pasta_templates = _backend_path() / "template_contrato"
        return {
            "success": False,
            "message": f"Template não encontrado para o modelo {modelo} em {pasta_templates}.",
            "caminho_docx": None,
            "error": "Template de contrato não disponível.",
        }

    try:
        dados = dados_contrato or _normalizar_dados_contrato(reserva_data)
        pasta_saida = Path(garantir_estrutura_hoje())
        nome_arquivo = _nome_arquivo_contrato(reserva_id, dados)
        caminho_docx = pasta_saida / nome_arquivo
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
    pasta_templates = _backend_path() / "template_contrato"
    nomes_template = TEMPLATE_MODELOS.get(modelo)
    if not nomes_template:
        return None

    for nome_template in nomes_template:
        template_path = pasta_templates / nome_template
        if template_path.exists():
            return template_path

    return _buscar_template_por_nome_normalizado(pasta_templates, modelo)


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
                    conteudo = _substituir_variaveis_negrito_xml(conteudo, variaveis)

                destino.writestr(item, conteudo)


def _substituir_variaveis_negrito_xml(conteudo, variaveis):
    try:
        root = ET.fromstring(conteudo)
    except ET.ParseError:
        texto = conteudo.decode("utf-8")
        for marcador, valor in variaveis.items():
            texto = texto.replace(marcador, escape(str(valor)))
        return texto.encode("utf-8")

    pais_com_runs = [
        elemento
        for elemento in root.iter()
        if any(filho.tag == _w("r") for filho in list(elemento))
    ]

    for pai in pais_com_runs:
        filhos = list(pai)
        novos_filhos = []
        alterado = False

        for filho in filhos:
            if filho.tag != _w("r"):
                novos_filhos.append(filho)
                continue

            runs = _substituir_run(filho, variaveis)
            if runs is None:
                novos_filhos.append(filho)
                continue

            novos_filhos.extend(runs)
            alterado = True

        if alterado:
            pai[:] = novos_filhos

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _substituir_run(run, variaveis):
    texto_node = None
    for filho in run:
        if filho.tag == _w("rPr"):
            continue
        if filho.tag != _w("t") or texto_node is not None:
            return None
        texto_node = filho

    if texto_node is None or not texto_node.text:
        return None

    partes = _segmentar_variaveis(texto_node.text, variaveis)
    if len(partes) == 1 and not partes[0][1]:
        return None

    return [
        _criar_run_texto(run, texto, negrito)
        for texto, negrito in partes
        if texto
    ]


def _segmentar_variaveis(texto, variaveis):
    marcadores = sorted(variaveis.keys(), key=len, reverse=True)
    partes = []
    posicao = 0

    while posicao < len(texto):
        ocorrencias = [
            (texto.find(marcador, posicao), marcador)
            for marcador in marcadores
            if texto.find(marcador, posicao) != -1
        ]

        if not ocorrencias:
            partes.append((texto[posicao:], False))
            break

        indice, marcador = min(ocorrencias, key=lambda item: (item[0], -len(item[1])))
        if indice > posicao:
            partes.append((texto[posicao:indice], False))

        partes.append((str(variaveis.get(marcador, "")), True))
        posicao = indice + len(marcador)

    return partes


def _criar_run_texto(run_original, texto, negrito):
    novo_run = ET.Element(_w("r"))
    rpr = run_original.find(_w("rPr"))

    if rpr is not None:
        novo_run.append(copy.deepcopy(rpr))

    if negrito:
        _garantir_negrito(novo_run)

    texto_node = ET.SubElement(novo_run, _w("t"))
    if texto[:1].isspace() or texto[-1:].isspace():
        texto_node.set(f"{{{XML_NS}}}space", "preserve")
    texto_node.text = texto
    return novo_run


def _garantir_negrito(run):
    rpr = run.find(_w("rPr"))
    if rpr is None:
        rpr = ET.Element(_w("rPr"))
        run.insert(0, rpr)

    for tag in ("b", "bCs"):
        elemento = rpr.find(_w(tag))
        if elemento is None:
            elemento = ET.SubElement(rpr, _w(tag))
        elemento.set(_w("val"), "1")


def _w(tag):
    return f"{{{W_NS}}}{tag}"


def _backend_path():
    project_backend = Path(__file__).resolve().parents[2] / "backend"
    if project_backend.exists():
        return project_backend
    return Path(__file__).resolve().parents[3] / "backend"


def _nome_arquivo_contrato(reserva_id, dados):
    cliente = dados.get("[nome_cliente]") or "Cliente"
    cliente_slug = _slug_arquivo(cliente) or "Cliente"
    return f"Contrato_Reserva_{reserva_id}_{cliente_slug}.docx"


def _slug_arquivo(valor):
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", texto).strip("_")


def _label_campo(marcador):
    return marcador.strip("[]").replace("_", " ").title()


def _valor_pendente(valor):
    texto = _normalizar_texto(valor)
    return "nao informado" in texto or "não informado" in texto


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
    if _quantidade_compradores(reserva_data) > 1 or _quantidade_fiadores(reserva_data) > 1:
        return "compradores"

    return "comprador_unico"


def _quantidade_compradores(reserva_data):
    proposta = _proposta_principal(reserva_data)
    compradores = (
        _buscar_valor(proposta, "compradores")
        or _buscar_valor(proposta, "clientes")
        or _buscar_valor(proposta, "cliente")
    )

    if isinstance(compradores, list):
        return len([comprador for comprador in compradores if comprador]) or 1
    if isinstance(compradores, dict):
        return len([comprador for comprador in compradores.values() if comprador]) or 1

    total = 1 if proposta.get("titular") else 0
    for pessoa in _associados(proposta):
        tipo = _normalizar_texto(pessoa.get("tipo", ""))
        if any(termo in tipo for termo in ("comprador", "cliente", "adquirente")):
            total += 1

    return total or 1


def _quantidade_fiadores(reserva_data):
    proposta = _proposta_principal(reserva_data)
    fiadores = _buscar_valor(proposta, "fiadores")

    if isinstance(fiadores, list):
        return len([fiador for fiador in fiadores if fiador])
    if isinstance(fiadores, dict):
        return len([fiador for fiador in fiadores.values() if fiador])

    return sum(
        1
        for pessoa in _associados(proposta)
        if "fiador" in _normalizar_texto(pessoa.get("tipo", ""))
    )


def _proposta_principal(dados):
    if not isinstance(dados, dict):
        return {}

    if any(chave in dados for chave in ("titular", "associados", "condicoes", "tipovenda")):
        return dados

    primeira_chave = next(iter(dados), None)
    if primeira_chave is None:
        return {}

    proposta = dados.get(primeira_chave)
    return proposta if isinstance(proposta, dict) else {}


def _associados(proposta):
    associados = proposta.get("associados", {})
    if isinstance(associados, dict):
        return [pessoa for pessoa in associados.values() if isinstance(pessoa, dict)]
    if isinstance(associados, list):
        return [pessoa for pessoa in associados if isinstance(pessoa, dict)]
    return []


def _buscar_template_por_nome_normalizado(pasta_templates, modelo):
    criterios = {
        "financiamento_comprador_unico": ("financiamento", ("comprador", "unico")),
        "financiamento_compradores": ("financiamento", ("compradores",)),
        "investimento_comprador_unico": ("investimento", ("comprador", "unico")),
        "investimento_compradores": ("investimento", ("compradores",)),
    }
    criterio = criterios.get(modelo)
    if not criterio or not pasta_templates.exists():
        return None

    tipo_contrato, termos = criterio
    for template_path in pasta_templates.glob("*.docx"):
        nome = _normalizar_nome_template(template_path.stem)
        if tipo_contrato in nome and all(termo in nome for termo in termos):
            return template_path

    return None


def _normalizar_nome_template(nome):
    texto = unicodedata.normalize("NFKD", str(nome))
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto).strip().lower()
    return texto


def _normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip().lower()
