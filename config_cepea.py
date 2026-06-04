# -*- coding: utf-8 -*-
"""
Configuração para sincronização CEPEA/ESALQ → Supabase

Fonte: scraping HTML via Selenium (contorna bloqueio 403)
Dados em BRL — salva direto em preco_brl.
Licença dos dados: CEPEA (CC BY-NC 4.0)

Estrutura das páginas:
  - Feijão: tabelas HTML padrão, tabela índice 0
  - Arroz:  tabelas com classe "imagenet-table", tabela índice 0
    cols: [data, valor_brl, var_dia, var_mes, valor_usd]
"""

FONTE_ID = 'e0cf35ee-344e-41bb-a84f-3b7198db79cd'

REGIAO_NACIONAL_ID = 'f6bb49e2-78db-4e2a-9668-11773cacd93c'  # Nacional

PRODUTOS = {
    'feijao': '334457f7-ceab-4e59-8ece-ae6a275d82f8',
    'arroz':  'db5c774a-15b9-4a7e-8d99-1a3384c56bfc',
}

CEPEA_CONFIG = [
    {
        'nome':       'Feijao Carioca',
        'produto_id': PRODUTOS['feijao'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'url':        'https://cepea.org.br/br/indicador/feijao.aspx',
        'moeda':      'BRL',
        'unidade':    'sc60kg',
        # Tabela HTML padrão — aguarda seletor CSS genérico
        'wait_css':   'table tbody tr td',
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
        # Tabela com classe imagenet-table — aguarda seletor específico
        'wait_css':   '.imagenet-table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,
    },
]
