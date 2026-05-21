import json
import os
from pathlib import Path

import httpx

from app.config.settings import AUTENTIQUE_DOCUMENTS_FILE, AUTENTIQUE_TOKEN


AUTENTIQUE_URL = "https://api.autentique.com.br/v2/graphql"


CRIAR_DOCUMENTO_MUTATION = """
mutation CreateDocumentMutation(
  $document: DocumentInput!,
  $signers: [SignerInput!]!,
  $file: Upload!
) {
  createDocument(
    sandbox: true,
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


def _status_simplificado(dados_documento):
    assinaturas = dados_documento.get("signatures", [])
    assinaturas_para_assinar = [
        assinatura
        for assinatura in assinaturas
        if (assinatura.get("action") or {}).get("name") == "SIGN"
    ]

    if any(assinatura.get("rejected") for assinatura in assinaturas):
        return "recusado"
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


def _salvar_documento(documento_id, dados_documento, caminho_docx=None):
    caminho = Path(AUTENTIQUE_DOCUMENTS_FILE)
    os.makedirs(caminho.parent, exist_ok=True)

    documentos = _carregar_documentos()
    documentos[documento_id] = {
        "id": documento_id,
        "nome": dados_documento.get("name"),
        "caminho_docx": str(caminho_docx) if caminho_docx else "",
        "status": _status_simplificado(dados_documento),
        "files": dados_documento.get("files"),
        "signatures": dados_documento.get("signatures", []),
    }
    caminho.write_text(json.dumps(documentos, ensure_ascii=False, indent=2), encoding="utf-8")


def status_assinatura_arquivo(caminho_docx):
    caminho = Path(caminho_docx)
    if caminho.suffix.lower() != ".docx":
        return None

    documentos = _carregar_documentos()
    registro = None
    caminho_normalizado = str(caminho)

    for item in documentos.values():
        if item.get("caminho_docx") == caminho_normalizado or item.get("nome") == caminho.name:
            registro = item
            break

    if not registro:
        return {"label": "Não assinado", "color": "#64748B"}

    status = registro.get("status")
    if status == "finalizado":
        return {"label": "Assinado", "color": "#22c55e"}
    if status == "recusado":
        return {"label": "Recusado", "color": "#ef4444"}
    return {"label": "Enviado para assinar", "color": "#f59e0b"}


def assinar_docx_autentique(caminho_docx, nome_assinante, email_assinante):
    caminho = Path(caminho_docx)
    if not caminho.exists():
        return _resposta(False, "falha", "Arquivo não encontrado.", error="arquivo_inexistente")
    if caminho.suffix.lower() != ".docx":
        return _resposta(False, "falha", "Envie apenas arquivos .docx.", error="extensao_invalida")
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
                    "delivery_method": "DELIVERY_METHOD_LINK",
                    "action": "SIGN",
                }
            ],
            "file": None,
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
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
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
