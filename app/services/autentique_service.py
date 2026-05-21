import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.config.settings import AUTENTIQUE_DOCUMENTS_FILE, AUTENTIQUE_SANDBOX, AUTENTIQUE_TOKEN


AUTENTIQUE_URL = "https://api.autentique.com.br/v2/graphql"


CRIAR_DOCUMENTO_MUTATION = """
mutation CreateDocumentMutation(
  $document: DocumentInput!,
  $signers: [SignerInput!]!,
  $file: Upload!,
  $sandbox: Boolean
) {
  createDocument(
    sandbox: $sandbox,
    document: $document,
    signers: $signers,
    file: $file
  ) {
    id
    name
    created_at
    files { original signed pades }
    signatures {
      public_id
      name
      email
      created_at
      action { name }
      link { short_link }
      viewed { created_at }
      signed { created_at }
      rejected { created_at reason }
    }
  }
}
"""


CONSULTAR_DOCUMENTO_QUERY = """
query ConsultarDocumento($id: UUID!) {
  document(id: $id) {
    id
    name
    created_at
    files { original signed pades }
    signatures {
      public_id
      name
      email
      created_at
      action { name }
      link { short_link }
      email_events {
        sent
        opened
        delivered
        refused
        reason
      }
      viewed { created_at }
      signed { created_at }
      rejected { created_at reason }
    }
  }
}
"""


def _resposta(success, status, message, documento_id=None, links=None, error=None, resposta=None):
    return {
        "success": success,
        "status": status,
        "message": message,
        "documento_id": documento_id,
        "links_assinatura": links or [],
        "error": error,
        "resposta_autentique": resposta,
    }


def _headers_autentique():
    token = AUTENTIQUE_TOKEN.strip()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _headers_download_autentique():
    headers = _headers_autentique()
    return headers or {}


def _mensagem_erro_graphql(resposta_json):
    erros = resposta_json.get("errors", [])
    if not erros:
        return None

    mensagens = " | ".join(erro.get("message", "") for erro in erros)
    mensagens_lower = mensagens.lower()
    if "unauthenticated" in mensagens_lower or "unauthorized" in mensagens_lower:
        return "Erro de autenticação com a Autentique. Verifique o token da API."
    if "not found" in mensagens_lower or "nao encontrado" in mensagens_lower:
        return "Documento não encontrado na Autentique."
    return mensagens or "Erro retornado pela Autentique."


def _post_graphql_json(operations, timeout=30):
    headers = _headers_autentique()
    if not headers:
        return None, _resposta(
            False,
            "falha",
            "Token da Autentique não configurado no .env.",
            error="token_ausente",
        )

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(AUTENTIQUE_URL, json=operations, headers=headers)
    except httpx.RequestError as ex:
        return None, _resposta(
            False,
            "falha",
            f"Erro de comunicação com a Autentique: {ex}",
            error=str(ex),
        )

    if response.status_code in (401, 403):
        return None, _resposta(
            False,
            "falha",
            "Erro de autenticação com a Autentique. Verifique o token da API.",
            error=response.text,
        )
    if response.status_code >= 400:
        return None, _resposta(
            False,
            "falha",
            f"Erro HTTP {response.status_code}: {response.text}",
            error=response.text,
        )

    try:
        resposta_json = response.json()
    except ValueError:
        return None, _resposta(False, "falha", "Resposta inválida da Autentique.", error=response.text)

    erro_graphql = _mensagem_erro_graphql(resposta_json)
    if erro_graphql:
        return None, _resposta(False, "falha", erro_graphql, error=json.dumps(resposta_json, ensure_ascii=False))

    return resposta_json, None


def _status_simplificado(dados_documento):
    assinaturas = dados_documento.get("signatures", [])
    assinaturas_para_assinar = [
        assinatura
        for assinatura in assinaturas
        if (assinatura.get("action") or {}).get("name") == "SIGN"
    ]

    if any(assinatura.get("rejected") for assinatura in assinaturas):
        return "recusado"
    if any(
        ((assinatura.get("email_events") or {}).get("refused"))
        for assinatura in assinaturas_para_assinar
    ):
        return "email_falhou"
    if assinaturas_para_assinar and all(
        assinatura.get("signed") for assinatura in assinaturas_para_assinar
    ):
        return "finalizado"
    if any(assinatura.get("viewed") or assinatura.get("signed") for assinatura in assinaturas):
        return "em_andamento"
    return "pendente"


def _links_dos_assinantes(dados_documento):
    links = []
    for assinatura in dados_documento.get("signatures", []):
        link = assinatura.get("link") or {}
        links.append(
            {
                "nome": assinatura.get("name"),
                "email": assinatura.get("email"),
                "public_id": assinatura.get("public_id"),
                "acao": (assinatura.get("action") or {}).get("name"),
                "link_assinatura": link.get("short_link"),
                "visualizado_em": (assinatura.get("viewed") or {}).get("created_at"),
                "assinado_em": (assinatura.get("signed") or {}).get("created_at"),
                "recusado_em": (assinatura.get("rejected") or {}).get("created_at"),
            }
        )
    return links


def _carregar_documentos():
    caminho = Path(AUTENTIQUE_DOCUMENTS_FILE)
    if not caminho.exists():
        return {}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _agora_iso():
    return datetime.now(timezone.utc).isoformat()


def _caminho_pdf_assinado(dados_documento, caminho_docx=None):
    caminho_original = Path(caminho_docx) if caminho_docx else None
    nome_base = dados_documento.get("name") or dados_documento.get("id") or "documento"
    stem = Path(nome_base).stem

    if caminho_original:
        pasta = caminho_original.parent
        if caminho_original.suffix.lower() == ".pdf" and caminho_original.stem.endswith("_assinado"):
            return caminho_original
        return pasta / f"{caminho_original.stem}_assinado.pdf"

    return Path(AUTENTIQUE_DOCUMENTS_FILE).parent / f"{stem}_assinado.pdf"


def _baixar_pdf_assinado(dados_documento, caminho_docx=None):
    if _status_simplificado(dados_documento) != "finalizado":
        return None, None

    arquivos = dados_documento.get("files") or {}
    url_pdf = arquivos.get("signed")
    if not url_pdf:
        return None, "A Autentique não retornou o PDF assinado."

    destino = _caminho_pdf_assinado(dados_documento, caminho_docx)
    if destino.exists() and destino.stat().st_size > 0:
        return str(destino), None

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            response = client.get(url_pdf, headers=_headers_download_autentique())
        if response.status_code >= 400:
            return None, f"Erro HTTP {response.status_code} ao baixar PDF assinado."
        destino.write_bytes(response.content)
        return str(destino), None
    except Exception as ex:
        return None, str(ex)


def _salvar_documento(documento_id, dados_documento, caminho_docx=None, caminho_pdf_assinado=None, erro_download=None):
    caminho = Path(AUTENTIQUE_DOCUMENTS_FILE)
    os.makedirs(caminho.parent, exist_ok=True)

    documentos = _carregar_documentos()
    registro_anterior = documentos.get(documento_id, {})
    caminho_pdf_assinado = caminho_pdf_assinado or registro_anterior.get("caminho_pdf_assinado", "")
    erro_download = erro_download or registro_anterior.get("erro_download_assinado", "")

    documentos[documento_id] = {
        "id": documento_id,
        "nome": dados_documento.get("name"),
        "caminho_docx": str(caminho_docx) if caminho_docx else "",
        "created_at": dados_documento.get("created_at"),
        "status": _status_simplificado(dados_documento),
        "files": dados_documento.get("files"),
        "signatures": dados_documento.get("signatures", []),
        "caminho_pdf_assinado": caminho_pdf_assinado,
        "erro_download_assinado": erro_download,
        "atualizado_em": _agora_iso(),
    }
    caminho.write_text(json.dumps(documentos, ensure_ascii=False, indent=2), encoding="utf-8")


def _registro_sort_key(registro):
    if registro.get("created_at"):
        return registro["created_at"]
    assinaturas = registro.get("signatures") or []
    for assinatura in assinaturas:
        if assinatura.get("created_at"):
            return assinatura["created_at"]
    return registro.get("atualizado_em") or ""


def _registro_por_caminho(caminho_docx):
    documentos = _carregar_documentos()
    caminho = Path(caminho_docx)
    caminho_normalizado = str(caminho)
    registros = [
        item
        for item in documentos.values()
        if (
            item.get("caminho_docx") == caminho_normalizado
            or item.get("caminho_pdf_assinado") == caminho_normalizado
            or item.get("nome") == caminho.name
            or Path(item.get("caminho_pdf_assinado") or "").name == caminho.name
        )
    ]
    if not registros:
        return None
    return max(registros, key=_registro_sort_key)


def _pdf_assinado_existe(registro):
    caminho = registro.get("caminho_pdf_assinado")
    return bool(caminho and Path(caminho).exists())


def tag_assinatura_arquivo(caminho_docx):
    caminho = Path(caminho_docx)
    if caminho.suffix.lower() != ".pdf":
        return "sem_tag"

    registro = _registro_por_caminho(caminho)
    if not registro:
        return "nao_assinado"

    status = registro.get("status")
    if status == "finalizado":
        return "assinado"
    if status == "recusado":
        return "recusado"
    if status == "email_falhou":
        return "email_falhou"
    return "enviado"


def status_assinatura_arquivo(caminho_docx):
    caminho = Path(caminho_docx)
    if caminho.suffix.lower() != ".pdf":
        return None

    registro = _registro_por_caminho(caminho)

    if not registro:
        return {"label": "Não assinado", "color": "#64748B"}

    status = registro.get("status")
    if status == "finalizado":
        return {"label": "Assinado", "color": "#22c55e"}
    if status == "recusado":
        return {"label": "Recusado", "color": "#ef4444"}
    if status == "email_falhou":
        return {"label": "E-mail falhou", "color": "#ef4444"}
    return {"label": "Enviado para assinar", "color": "#f59e0b"}


def listar_contratos_assinados():
    documentos = _carregar_documentos()
    assinados = []

    for registro in documentos.values():
        if registro.get("status") != "finalizado":
            continue

        caminho_pdf = registro.get("caminho_pdf_assinado", "")
        caminho_docx = registro.get("caminho_docx", "")
        caminho_arquivo = caminho_pdf if caminho_pdf and Path(caminho_pdf).exists() else caminho_docx

        assinados.append(
            {
                "id": registro.get("id", ""),
                "nome": registro.get("nome", ""),
                "caminho_docx": caminho_docx,
                "caminho_pdf_assinado": caminho_pdf,
                "caminho_arquivo": caminho_arquivo,
                "created_at": registro.get("created_at", ""),
                "atualizado_em": registro.get("atualizado_em", ""),
                "assinaturas": registro.get("signatures", []),
                "erro_download_assinado": registro.get("erro_download_assinado", ""),
            }
        )

    return sorted(assinados, key=_registro_sort_key, reverse=True)


def consultar_documento_autentique(documento_id):
    operations = {
        "query": CONSULTAR_DOCUMENTO_QUERY,
        "variables": {"id": documento_id},
    }
    resposta_json, erro = _post_graphql_json(operations)
    if erro:
        return erro

    documento = resposta_json.get("data", {}).get("document")
    if not documento:
        return _resposta(
            False,
            "falha",
            "Documento não encontrado na Autentique.",
            documento_id=documento_id,
            error=json.dumps(resposta_json, ensure_ascii=False),
        )

    return _resposta(
        True,
        _status_simplificado(documento),
        "Status consultado com sucesso.",
        documento_id=documento.get("id"),
        links=_links_dos_assinantes(documento),
        resposta=documento,
    )


def atualizar_status_assinaturas_autentique():
    documentos = _carregar_documentos()
    if not documentos:
        return {
            "success": True,
            "total": 0,
            "atualizados": 0,
            "assinados": 0,
            "falhas": [],
            "message": "Nenhum documento enviado para assinatura.",
        }

    atualizados = 0
    assinados = 0
    baixados = 0
    falhas = []

    for documento_id, registro in list(documentos.items()):
        if registro.get("status") == "finalizado" and _pdf_assinado_existe(registro):
            assinados += 1
            continue

        resultado = consultar_documento_autentique(documento_id)
        if not resultado["success"]:
            falhas.append(
                {
                    "documento_id": documento_id,
                    "nome": registro.get("nome", ""),
                    "erro": resultado.get("error") or resultado["message"],
                }
            )
            continue

        documento = resultado["resposta_autentique"]
        caminho_pdf_assinado = ""
        erro_download = ""
        if resultado["status"] == "finalizado":
            caminho_pdf_assinado, erro_download = _baixar_pdf_assinado(documento, registro.get("caminho_docx"))
            if caminho_pdf_assinado:
                baixados += 1
            elif erro_download:
                falhas.append(
                    {
                        "documento_id": documento_id,
                        "nome": registro.get("nome", ""),
                        "erro": erro_download,
                    }
                )

        _salvar_documento(
            documento_id,
            documento,
            registro.get("caminho_docx"),
            caminho_pdf_assinado=caminho_pdf_assinado,
            erro_download=erro_download,
        )
        atualizados += 1
        if resultado["status"] == "finalizado":
            assinados += 1

    message = f"{atualizados} documento(s) verificado(s)."
    if assinados:
        message = f"{message} {assinados} assinado(s)."
    if baixados:
        message = f"{message} {baixados} PDF(s) baixado(s)."
    if falhas:
        message = f"{message} {len(falhas)} falha(s)."

    return {
        "success": not falhas,
        "total": len(documentos),
        "atualizados": atualizados,
        "assinados": assinados,
        "baixados": baixados,
        "falhas": falhas,
        "message": message,
    }


def assinar_pdf_autentique(caminho_pdf, nome_assinante, email_assinante):
    caminho = Path(caminho_pdf)
    if not caminho.exists():
        return _resposta(False, "falha", "Arquivo não encontrado.", error="arquivo_inexistente")
    if caminho.suffix.lower() != ".pdf":
        return _resposta(False, "falha", "Envie apenas arquivos PDF.", error="extensao_invalida")
    if not nome_assinante.strip() or not email_assinante.strip():
        return _resposta(False, "falha", "Informe nome e e-mail do assinante.", error="assinante_invalido")

    headers = _headers_autentique()
    if not headers:
        return _resposta(
            False,
            "falha",
            "Token da Autentique não configurado no .env.",
            error="token_ausente",
        )

    operations = {
        "query": CRIAR_DOCUMENTO_MUTATION,
        "variables": {
            "document": {"name": caminho.name},
            "signers": [
                {
                    "name": nome_assinante.strip(),
                    "email": email_assinante.strip(),
                    "delivery_method": "DELIVERY_METHOD_EMAIL",
                    "action": "SIGN",
                }
            ],
            "file": None,
            "sandbox": AUTENTIQUE_SANDBOX,
        },
    }

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(
                AUTENTIQUE_URL,
                data={
                    "operations": json.dumps(operations),
                    "map": json.dumps({"file": ["variables.file"]}),
                },
                files={
                    "file": (
                        caminho.name,
                        caminho.read_bytes(),
                        "application/pdf",
                    )
                },
                headers=headers,
            )
    except httpx.RequestError as ex:
        return _resposta(
            False,
            "falha",
            f"Erro de comunicação com a Autentique: {ex}",
            error=str(ex),
        )

    if response.status_code in (401, 403):
        return _resposta(
            False,
            "falha",
            "Erro de autenticação com a Autentique. Verifique o token da API.",
            error=response.text,
        )
    if response.status_code >= 400:
        return _resposta(False, "falha", f"Erro HTTP {response.status_code}: {response.text}", error=response.text)

    try:
        resposta_json = response.json()
    except ValueError:
        return _resposta(False, "falha", "Resposta inválida da Autentique.", error=response.text)

    erro_graphql = _mensagem_erro_graphql(resposta_json)
    if erro_graphql:
        return _resposta(False, "falha", erro_graphql, error=json.dumps(resposta_json, ensure_ascii=False))

    documento = resposta_json.get("data", {}).get("createDocument")
    if not documento:
        return _resposta(
            False,
            "falha",
            "A Autentique respondeu, mas não retornou os dados do documento.",
            error=json.dumps(resposta_json, ensure_ascii=False),
        )

    documento_id = documento.get("id")
    if not documento_id:
        return _resposta(
            False,
            "falha",
            "A Autentique criou a resposta, mas não retornou o id do documento.",
            error=json.dumps(documento, ensure_ascii=False),
            resposta=documento,
        )

    _salvar_documento(documento_id, documento, caminho)
    links = _links_dos_assinantes(documento)
    return _resposta(
        True,
        _status_simplificado(documento),
        "Documento enviado para assinatura com sucesso.",
        documento_id=documento_id,
        links=links,
        resposta=documento,
    )


assinar_docx_autentique = assinar_pdf_autentique
