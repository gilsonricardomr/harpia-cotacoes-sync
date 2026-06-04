# -*- coding: utf-8 -*-
"""
Configuração para sincronização CEPEA/ESALQ → Supabase

Fonte: scraping do HTML de https://cepea.org.br/br/indicador/{produto}.aspx
Sem API pública (a API oficial custa R$10.500/ano).
Dados em BRL — o trigger NÃO precisa converter, salvamos direto em preco_brl.
Licença dos dados: CEPEA (CC BY-NC 4.0)

Produtos cobertos:
  - Feijão Carioca (Peneira 12, notas 9+): média das regiões mapeadas
  - Arroz em Casca CEPEA/IRGA-RS: saca 50kg, posto indústria RS
"""

FONTE_ID = 'e0cf35ee-344e-41bb-a84f-3b7198db79cd'  # CEPEA no banco

# Região base para feijão — usamos São Paulo (mapeada) como proxy nacional
# Para arroz usamos Nacional pois é indicador único
REGIAO_SP_ID       = '0aa3e7f9-ae3b-430a-81ec-a3c22106a3e5'  # São Paulo
REGIAO_NACIONAL_ID = 'f6bb49e2-78db-4e2a-9668-11773cacd93c'  # Nacional

PRODUTOS = {
    'feijao': '334457f7-ceab-4e59-8ece-ae6a275d82f8',
    'arroz':  'a032936e-4064-49da-8ee2-8f2298540a10',
}

# Cada entrada define como extrair o indicador principal da página
CEPEA_CONFIG = [
    {
        'nome':       'Feijao Carioca',
        'produto_id': PRODUTOS['feijao'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'url':        'https://cepea.org.br/br/indicador/feijao.aspx',
        'moeda':      'BRL',
        'unidade':    'sc60kg',
        # Extrai da 1a tabela (Peneira 12, notas 9+), faz média das regiões do dia
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  2,
    },
    {
        'nome':       'Arroz em Casca',
        'produto_id': PRODUTOS['arroz'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'url':        'https://cepea.org.br/br/indicador/arroz.aspx',
        'moeda':      'BRL',
        'unidade':    'sc50kg',
        # Extrai da 1a tabela (Indicador IRGA-RS), 1a linha = dia mais recente
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,
    },
]
