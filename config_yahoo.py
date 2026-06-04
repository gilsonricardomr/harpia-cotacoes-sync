# -*- coding: utf-8 -*-
"""
Configuração para sincronização Yahoo Finance → Supabase

IMPORTANTE — unidades:
  ZS=F (Soja), ZC=F (Milho), KC=F (Café), ZW=F (Trigo):
    Cotados em USd/bushel ou USd/lb (centavos de USD na CBOT).
    divisor=100 converte USd → USD antes de salvar.
  LE=F (Boi Gordo): cotado em USD/cwt — já em dólares, divisor=1.

  O trigger calcular_preco_convertido cuida do USD → BRL automaticamente.
"""

FONTE_ID = 'b169f3b3-7fb0-48cb-867e-c03e3907c5c7'
REGIAO_NACIONAL_ID = '689348a6-e539-4d57-9f68-9bf8b9a437c1'

PRODUTOS = {
    'boi_gordo':    '9e382636-0b57-482b-a836-522da43b6228',
    'cafe_arabica': 'b65effe8-94fb-4f73-8404-7bdeddb74565',
    'soja':         'f1fe7635-add9-4a03-b542-a27a57848682',
    'milho':        '553e75be-a732-4ff5-9b93-11bb8861114a',
    'trigo':        '01340329-fc80-4598-a94a-80e3fb7cf9dc',
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
        'nome':       'Trigo',
        'ticker':     'ZW=F',
        'produto_id': PRODUTOS['trigo'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'moeda':      'USD',
        'divisor':    100,   # USd/bushel → USD/bushel
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
