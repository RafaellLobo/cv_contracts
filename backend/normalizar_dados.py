def normalizar_dados_cvcrm(dados):
    def apenas_digitos(valor):
        if valor is None:
            return ""
        return re.sub(r"\D", "", str(valor))

    def texto(valor, padrao):
        if valor is None or valor == "":
            return padrao
        return str(valor)

    def formatar_cpf(valor):
        digitos = apenas_digitos(valor)
        if len(digitos) != 11:
            return texto(valor, "CPF NÃO INFORMADO")
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"

    def formatar_cnpj(valor):
        digitos = apenas_digitos(valor)
        if len(digitos) != 14:
            return texto(valor, "CNPJ NÃO INFORMADO")
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"

    def formatar_cep(valor):
        digitos = apenas_digitos(valor)
        if len(digitos) != 8:
            return texto(valor, "CEP NÃO INFORMADO")
        return f"{digitos[:5]}-{digitos[5:]}"

    def formatar_telefone(valor):
        digitos = apenas_digitos(valor)

        if not digitos:
            return "TELEFONE NÃO INFORMADO"

        if digitos.startswith("55") and len(digitos) > 11:
            digitos = digitos[2:]

        if len(digitos) == 11:
            return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"

        if len(digitos) == 10:
            return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"

        return str(valor)

    def formatar_moeda(valor):
        if valor is None or valor == "":
            return "VALOR NÃO INFORMADO"

        try:
            numero = float(str(valor).replace(",", "."))
            return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except ValueError:
            return str(valor)

    def formatar_data(valor):
        if not valor:
            return "DATA NÃO INFORMADA"

        formatos = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for formato in formatos:
            try:
                data = datetime.strptime(str(valor), formato)
                return data.strftime("%d/%m/%Y")
            except ValueError:
                pass

        return str(valor)

    def pegar_primeira_proposta(dados):
        if not isinstance(dados, dict):
            return {}

        if "imobiliaria" in dados or "titular" in dados:
            return dados

        primeira_chave = next(iter(dados), None)

        if primeira_chave is None:
            return {}

        return dados.get(primeira_chave, {})

    proposta = pegar_primeira_proposta(dados)

    imobiliaria = proposta.get("imobiliaria", {})
    titular = proposta.get("titular", {})
    unidade = proposta.get("unidade", {})
    condicoes = proposta.get("condicoes", {})
    corretor = proposta.get("corretor", {})
    comissoes = proposta.get("comissoes", {})
    associados = proposta.get("associados", {})

    fiador = next(
        (
            pessoa for pessoa in associados.values()
            if pessoa.get("tipo", "").lower() == "fiador"
        ),
        {}
    )

    series = condicoes.get("series", [])

    serie_ato = next(
        (s for s in series if s.get("serie") == "Ato"),
        {}
    )

    serie_parcelas = next(
        (s for s in series if "Parcelas" in s.get("serie", "")),
        {}
    )

    serie_chaves = next(
        (s for s in series if s.get("serie") == "Chaves"),
        {}
    )

    def valor_float(valor):
        try:
            return float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            return 0.0

    valor_ato = valor_float(serie_ato.get("valor_serie"))
    valor_parcelas = valor_float(serie_parcelas.get("valor_serie"))

    entrada_total = valor_ato + valor_parcelas

    return {
        # EMPRESA
        "[nome_empresa]": texto(imobiliaria.get("nome"), "NOME DA EMPRESA"),
        "[cnpj_empresa]": formatar_cnpj(imobiliaria.get("cnpj")),

        # COMPRADOR
        "[nome_cliente]": texto(titular.get("nome"), "NOME DO CLIENTE"),
        "[cpf_cliente]": formatar_cpf(titular.get("documento")),
        "[email_cliente]": texto(titular.get("email"), "EMAIL NÃO INFORMADO"),
        "[telefone_cliente]": formatar_telefone(
            titular.get("telefone") or titular.get("celular")
        ),

        "[nacionalidade_cliente]": texto(titular.get("nacionalidade"), "NACIONALIDADE NÃO INFORMADA"),
        "[estado_civil_cliente]": texto(titular.get("estado_civil"), "ESTADO CIVIL NÃO INFORMADO"),
        "[profissao_cliente]": texto(
            titular.get("profissao") or titular.get("profissao_select"),
            "PROFISSÃO NÃO INFORMADA"
        ),

        "[orgao_rg_cliente]": texto(titular.get("rg_orgao_emissor"), "ÓRGÃO RG NÃO INFORMADO"),
        "[uf_rg_cliente]": "UF RG NÃO INFORMADA",

        "[rua_endereco_cliente]": texto(titular.get("endereco"), "RUA NÃO INFORMADA"),
        "[num_endereco_cliente]": texto(titular.get("numero"), "NÚMERO NÃO INFORMADO"),
        "[bairro_endereco_cliente]": texto(titular.get("bairro"), "BAIRRO NÃO INFORMADO"),
        "[municipio_endereco_cliente]": texto(titular.get("cidade"), "MUNICÍPIO NÃO INFORMADO"),
        "[estado_endereco_cliente]": texto(titular.get("estado"), "ESTADO NÃO INFORMADO"),
        "[cep_endereco_cliente]": formatar_cep(titular.get("cep")),

        # FIADOR
        "[nome_fiador]": texto(fiador.get("nome"), "NOME DO FIADOR NÃO INFORMADO"),
        "[cpf_fiador]": formatar_cpf(fiador.get("documento")),
        "[email_fiador]": texto(fiador.get("email"), "EMAIL DO FIADOR NÃO INFORMADO"),
        "[telefone_fiador]": formatar_telefone(
            fiador.get("telefone") or fiador.get("celular")
        ),

        "[nacionalidade_fiador]": texto(fiador.get("nacionalidade"), "NACIONALIDADE DO FIADOR NÃO INFORMADA"),
        "[estado_civil_fiador]": texto(fiador.get("estado_civil"), "ESTADO CIVIL DO FIADOR NÃO INFORMADO"),
        "[profissao_fiador]": texto(
            fiador.get("profissao") or fiador.get("profissao_select"),
            "PROFISSÃO DO FIADOR NÃO INFORMADA"
        ),

        "[orgao_rg_fiador]": texto(fiador.get("rg_orgao_emissor"), "ÓRGÃO RG DO FIADOR NÃO INFORMADO"),
        "[uf_rg_fiador]": "UF RG DO FIADOR NÃO INFORMADA",

        "[rua_endereco_fiador]": texto(fiador.get("endereco"), "RUA DO FIADOR NÃO INFORMADA"),
        "[num_endereco_fiador]": texto(fiador.get("numero"), "NÚMERO DO FIADOR NÃO INFORMADO"),
        "[bairro_endereco_fiador]": texto(fiador.get("bairro"), "BAIRRO DO FIADOR NÃO INFORMADO"),
        "[municipio_endereco_fiador]": texto(fiador.get("cidade"), "MUNICÍPIO DO FIADOR NÃO INFORMADO"),
        "[estado_endereco_fiador]": texto(fiador.get("estado"), "ESTADO DO FIADOR NÃO INFORMADO"),
        "[cep_endereco_fiador]": formatar_cep(fiador.get("cep")),

        # IMÓVEL
        "[nome_empreendimento]": texto(unidade.get("empreendimento"), "EMPREENDIMENTO NÃO INFORMADO"),
        "[unidade]": texto(unidade.get("unidade"), "UNIDADE NÃO INFORMADA"),
        "[bloco_imovel]": texto(unidade.get("bloco"), "BLOCO NÃO INFORMADO"),
        "[matricula_empreendimento]": texto(unidade.get("matricula"), "MATRÍCULA NÃO INFORMADA"),

        "[rua_imovel]": "RUA DO IMÓVEL NÃO INFORMADA",
        "[numero_imovel]": "NÚMERO DO IMÓVEL NÃO INFORMADO",
        "[descricao_unidade_memorial]": texto(
            unidade.get("tipologia"),
            "DESCRIÇÃO DA UNIDADE NÃO INFORMADA"
        ),

        # CONTRATO / RESERVA
        "[valor_contrato]": formatar_moeda(condicoes.get("valor_contrato")),
        "[valor_contrato_extenso]": "VALOR POR EXTENSO NÃO INFORMADO",
        "[data_criacao]": formatar_data(proposta.get("data")),

        # ENTRADA
        "[entrada_total]": formatar_moeda(entrada_total),
        "[entrada_total_extenso]": "ENTRADA POR EXTENSO NÃO INFORMADA",

        "[valor_entrada_vista]": formatar_moeda(serie_ato.get("valor_serie")),
        "[valor_entrada_vista_extenso]": "VALOR DE ENTRADA À VISTA POR EXTENSO NÃO INFORMADO",
        "[data_vencimento_entrada_vista]": formatar_data(serie_ato.get("vencimento")),

        # PARCELAS
        "[entrada_parcelada_total]": formatar_moeda(serie_parcelas.get("valor_serie")),
        "[entrada_parcelada_total_extenso]": "ENTRADA PARCELADA POR EXTENSO NÃO INFORMADA",
        "[quantidade_parcelas_entrada]": texto(serie_parcelas.get("quantidade"), "QUANTIDADE NÃO INFORMADA"),
        "[quantidade_parcelas_entrada_extenso]": "QUANTIDADE POR EXTENSO NÃO INFORMADA",
        "[valor_parcela_entrada]": formatar_moeda(serie_parcelas.get("valor")),
        "[valor_parcela_entrada_extenso]": "VALOR DA PARCELA POR EXTENSO NÃO INFORMADO",
        "[data_primeiro_vencimento_parcela_entrada]": formatar_data(serie_parcelas.get("vencimento")),

        # FGTS / MCMV / COHAPAR
        "[valor_fgts]": "0,00",
        "[valor_fgts_extenso]": "ZERO REAIS",
        "[valor_mcmv]": "0,00",
        "[valor_mcmv_extenso]": "ZERO REAIS",
        "[valor_cohapar]": "20.000,00",

        # FINANCIAMENTO
        "[valor_financiamento]": formatar_moeda(serie_chaves.get("valor_serie")),
        "[valor_financiamento_extenso]": "VALOR DO FINANCIAMENTO POR EXTENSO NÃO INFORMADO",

        # CORRETAGEM
        "[valor_corretagem]": formatar_moeda(
            comissoes.get("comissao_valortotal") or proposta.get("valor_comissao")
        ),
        "[nome_imobiliaria_intermediadora]": texto(
            corretor.get("imobiliaria") or imobiliaria.get("nome"),
            "IMOBILIÁRIA NÃO INFORMADA"
        ),

        # BANCO
        "[agencia_empresa]": "AGÊNCIA NÃO INFORMADA",
        "[conta_corrente_empresa]": "CONTA CORRENTE NÃO INFORMADA",
        "[banco_empresa]": "BANCO NÃO INFORMADO",
        "[pix_empresa]": "PIX NÃO INFORMADO",

        # RENDA
        "[renda_formal_cliente]": formatar_moeda(titular.get("renda_familiar")),
        "[renda_formal_cliente_extenso]": "RENDA FORMAL POR EXTENSO NÃO INFORMADA",
    }
