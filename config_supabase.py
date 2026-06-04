"""
Configuração de mapeamento de IDs para o banco Supabase
"""

FONTE_ID = "b7b6ec49-f8cd-4d9f-adda-1ddfeba5e78c"

PRODUTOS = {
    "Milho": "553e75be-a732-4ff5-9b93-11bb8861114a",
    "Soja": "f1fe7635-add9-4a03-b542-a27a57848682",
    "Sorgo": "8a539aee-7713-4c17-867e-4b19ceb0bdcc"
}

REGIOES = {
    "Buritis, MG": "f4cbfe93-f918-49da-9d0b-d53a55b62d71",
    "Campinas": "5fde9780-8301-40f7-9bea-1a0c3e95ceca",
    "Centro Goiano": "c21eddf2-3b16-491d-8c55-3f2f8ede1683",
    "Chicago Futuros": "689348a6-e539-4d57-9f68-9bf8b9a437c1",
    "Leste Goiano": "cc5c2445-45a9-4d62-b3a0-8ee7519fcc81",
    "Mato Grosso do Sul": "947bc75d-9a13-48eb-9f4a-7ff6c6ad7fd8",
    "Noroeste de Minas": "31fa2384-b0aa-4e95-a418-5954872debed",
    "Norte Mato-grossense": "5da80100-f983-4472-a73a-6b1c2e2bccb3",
    "Oeste de Minas": "c8c06115-c7f1-4587-93c7-809ac87e6007",
    "Paranagua": "d24ef21e-e1ef-4dde-a34c-58d3054e364c",
    "Ribeirao Preto": "2889f4e1-7d0f-4d7d-bf49-c049ffb12873",
    "Sao Paulo": "0aa3e7f9-ae3b-430a-81ec-a3c22106a3e5",
    "Sudeste MT": "b72ed7cf-28c2-4685-a780-d8cd85fd76a3",
    "Sul Goiano": "634a455b-2b07-49a1-acaf-140122c1700c",
    "Sul/Sudoeste de Minas": "d5178d0f-1b72-48ad-9937-66319ce2f91b",
    "Triangulo Mineiro": "9f0bece6-66ca-4fe3-a72f-468f86b788ce",
    "Triangulo Mineiro/Alto Paranaiba": "9f0bece6-66ca-4fe3-a72f-468f86b788ce",
    "Metropolitana de Sao Paulo": "0aa3e7f9-ae3b-430a-81ec-a3c22106a3e5",
    "Sudoeste de Mato Grosso do Sul": "947bc75d-9a13-48eb-9f4a-7ff6c6ad7fd8",
}

def obter_regiao_id(nome_regiao):
    return REGIOES.get(nome_regiao)

def obter_produto_id(nome_produto):
    return PRODUTOS.get(nome_produto)

def listar_regioes_mapeadas():
    return list(REGIOES.keys())
