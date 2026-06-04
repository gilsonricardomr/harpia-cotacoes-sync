# -*- coding: utf-8 -*-
"""
Configuração para sincronização Yahoo Finance → Supabase
Fonte: API yfinance (sem autenticação, sem limite de requisições)
"""

# ID da fonte Yahoo Finance no banco
FONTE_ID = 'yahoo-finance-001'  # ajuste para o UUID real em mercado_fontes

# Região "Nacional" (commodities internacionais)
REGIAO_NACIONAL_ID = '689348a6-e539-4d57-9f68-9bf8b9a437c1'

# IDs de produtos (mesmos do config_investing)
PRODUTOS = {
    'boi_gordo':    '9e382636-0b57-482b-a836-522da43b6228',
    'cafe_arabica': 'b65effe8-94fb-4f73-8404-7bdeddb74565',
    'soja':         'f1fe7635-add9-4a03-b542-a27a57848682',
    'milho':        '553e75be-a732-4ff5-9b93-11bb8861114a',
}

# Mapeamento ticker Yahoo → produto_id + regiao_id
# Nota: LE=F = Live Cattle (boi gordo). GF=F = Feeder Cattle (boi magro) — nao usar
YAHOO_CONFIG = [
    {
        'nome':       'Soja',
        'ticker':     'ZS=F',
        'produto_id': PRODUTOS['soja'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
    {
        'nome':       'Milho',
        'ticker':     'ZC=F',
        'produto_id': PRODUTOS['milho'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
    {
        'nome':       'Cafe Arabica',
        'ticker':     'KC=F',
        'produto_id': PRODUTOS['cafe_arabica'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
    {
        'nome':       'Boi Gordo',
        'ticker':     'LE=F',
        'produto_id': PRODUTOS['boi_gordo'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
]
