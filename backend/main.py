import json
from pathlib import Path

if __package__:
    from .contrato_pdf import gerar_contrato
    from .cvcrm_client import CVCRMClient
    from .normalizar_dados import normalizar_dados_cvcrm
else:
    from contrato_pdf import gerar_contrato
    from cvcrm_client import CVCRMClient
    from normalizar_dados import normalizar_dados_cvcrm


BASE_DIR = Path(__file__).resolve().parent

def main():
    reserva_id = 4331
    client = CVCRMClient()

    resposta_api = client.buscar_reserva(reserva_id)

    with (BASE_DIR / "api_data.json").open("w", encoding="utf-8") as f:
        json.dump(resposta_api, f)

    dados_contrato = normalizar_dados_cvcrm(resposta_api)

    gerar_contrato(
        dados=dados_contrato,
        output_path=BASE_DIR / "output" / f"contrato_reserva_{reserva_id}.pdf"
    )
    print("Contrato gerado com sucesso.")

if __name__ == "__main__":
    main()
