# -*- coding: utf-8 -*-
"""
Configuração para sincronização Yahoo Finance → Supabase

IMPORTANTE — unidades:
  ZS=F (Soja)  e ZC=F (Milho): cotados em USd/bushel (centavos de USD).
  KC=F (Café): cotado em USd/lb (centavos de USD).
  LE=F (Boi Gordo): cotado em USD/cwt (dólares — sem divisor).

  O yfinance retorna o valor como aparece na CBOT (ex: soja 1126 = 1126 USd).
  Dividimos por 100 para converter USd → USD antes de salvar no banco.
  O trigger calcular_preco_convertido cuida do USD → BRL automaticamente.
"""

FONTE_ID = 'b169f3b3-7fb0-48cb-867e-c03e3907c5c7'
REGIAO_NACIONAL_ID = '689348a6-e539-4d57-9f68-9bf8b9a437c1'

PRODUTOS = {
    'boi_gordo':    '9e382636-0b57-482b-a836-522da43b6228',
    'cafe_arabica': 'b65effe8-94fb-4f73-8404-7bdeddb74565',
    'soja':         'f1fe7635-add9-4a03-b542-a27a57848682',
    'milho':        '553e75be-a732-4ff5-9b93-11bb8861114a',
}

YAHOO_CONFIG = [
    {
        'nome':       'Soja',
        'ticker':     'ZS=F',
        'produto_id': PRODUTOS['soja'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
        'divisor':    100,   # USd/bushel → USD/bushel
    },
    {
        'nome':       'Milho',
        'ticker':     'ZC=F',
        'produto_id': PRODUTOS['milho'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
        'divisor':    100,   # USd/bushel → USD/bushel
    },
    {
        'nome':       'Cafe Arabica',
        'ticker':     'KC=F',
        'produto_id': PRODUTOS['cafe_arabica'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
        'divisor':    100,   # USd/lb → USD/lb
    },
    {
        'nome':       'Boi Gordo',
        'ticker':     'LE=F',
        'produto_id': PRODUTOS['boi_gordo'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
        'divisor':    1,     # USD/cwt — já em dólares
    },
]
