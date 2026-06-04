# -*- coding: utf-8 -*-
"""
Configuração de IDs para sincronização Investing.com → Supabase
"""

FONTE_ID = 'e9981e67-669b-4394-9ac9-7be73f384e53'
REGIAO_NACIONAL_ID = '689348a6-e539-4d57-9f68-9bf8b9a437c1'

PRODUTOS = {
    'boi_gordo':    '9e382636-0b57-482b-a836-522da43b6228',
    'cafe_arabica': 'b65effe8-94fb-4f73-8404-7bdeddb74565',
    'soja':         'f1fe7635-add9-4a03-b542-a27a57848682',
    'milho':        '553e75be-a732-4ff5-9b93-11bb8861114a',
}

SCRAPING_CONFIG = [
    {
        'nome': 'Café Arábica',
        'produto_id': PRODUTOS['cafe_arabica'],
        'regiao_id': REGIAO_NACIONAL_ID,
        'url_atual':     'https://br.investing.com/commodities/arabica-coffee-4-5',
        'url_historico': 'https://br.investing.com/commodities/arabica-coffee-4-5-historical-data',
        'tipo': 'cotacao',
    },
    {
        'nome': 'Milho',
        'produto_id': PRODUTOS['milho'],
        'regiao_id': REGIAO_NACIONAL_ID,
        'url_atual':     'https://br.investing.com/commodities/us-corn?cid=964522',
        'url_historico': 'https://br.investing.com/commodities/us-corn-historical-data?cid=964522',
        'tipo': 'cotacao',
    },
    {
        'nome': 'Soja',
        'produto_id': PRODUTOS['soja'],
        'regiao_id': REGIAO_NACIONAL_ID,
        'url_atual':     'https://br.investing.com/commodities/us-soybeans?cid=964523',
        'url_historico': 'https://br.investing.com/commodities/us-soybeans-historical-data?cid=964523',
        'tipo': 'cotacao',
    },
    {
        'nome': 'Boi Gordo',
        'produto_id': PRODUTOS['boi_gordo'],
        'regiao_id': REGIAO_NACIONAL_ID,
        'url_atual':     'https://br.investing.com/commodities/live-cattle?cid=964528',
        'url_historico': 'https://br.investing.com/commodities/live-cattle-historical-data?cid=964528',
        'tipo': 'cotacao',
    },
]
