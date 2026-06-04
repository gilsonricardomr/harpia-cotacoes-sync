# -*- coding: utf-8 -*-
"""
Configuração para sincronização Alpha Vantage → Supabase
Fonte: API REST gratuita (25 req/dia no plano free — suficiente para 4 commodities)
API Key: configurada via variável de ambiente ALPHA_VANTAGE_KEY
"""

FONTE_ID = '70a47e77-abc1-49a3-8775-235975e78420'

REGIAO_NACIONAL_ID = '689348a6-e539-4d57-9f68-9bf8b9a437c1'

PRODUTOS = {
    'boi_gordo':    '9e382636-0b57-482b-a836-522da43b6228',
    'cafe_arabica': 'b65effe8-94fb-4f73-8404-7bdeddb74565',
    'soja':         'f1fe7635-add9-4a03-b542-a27a57848682',
    'milho':        '553e75be-a732-4ff5-9b93-11bb8861114a',
}

# Docs: https://www.alphavantage.co/documentation/#commodities
ALPHA_CONFIG = [
    {
        'nome':       'Soja',
        'function':   'SOYBEANS',
        'produto_id': PRODUTOS['soja'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
    {
        'nome':       'Milho',
        'function':   'CORN',
        'produto_id': PRODUTOS['milho'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
    {
        'nome':       'Cafe Arabica',
        'function':   'COFFEE',
        'produto_id': PRODUTOS['cafe_arabica'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
    {
        'nome':       'Boi Gordo',
        'function':   'LIVE_CATTLE',
        'produto_id': PRODUTOS['boi_gordo'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
    },
]

BASE_URL = 'https://www.alphavantage.co/query'
