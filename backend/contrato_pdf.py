from pathlib import Path
import mammoth
from docx import Document


def substituir_texto_docx(doc, variaveis):

    def substituir_em_paragrafos(paragrafos):
        for paragrafo in paragrafos:
            for run in paragrafo.runs:
                for marcador, valor in variaveis.items():
                    if marcador in run.text:
                        run.text = run.text.replace(marcador, str(valor))

    substituir_em_paragrafos(doc.paragraphs)

    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                substituir_em_paragrafos(celula.paragraphs)

    return doc

def gerar_contrato(dados, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    template_path = Path(__file__).resolve().parent / "template_contrato" / "contrato_financiamento_comprador_unico.docx"

    doc = Document(template_path)

    variaveis = dados

    doc = substituir_texto_docx(doc, variaveis)

    docx_saida = output_path.with_suffix(".docx")
    doc.save(docx_saida)

    print("Arquivo .docx gerado em:", docx_saida.resolve())
