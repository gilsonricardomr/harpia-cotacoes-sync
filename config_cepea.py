# -*- coding: utf-8 -*-
"""
Configuração para sincronização CEPEA/ESALQ → Supabase

Produtos com tabela disponível no CEPEA:
  ✅ Café Arábica   — cepea.org.br/br/indicador/cafe.aspx
  ✅ Milho          — cepea.org.br/br/indicador/milho.aspx
  ✅ Trigo          — cepea.org.br/br/indicador/trigo.aspx
  ✅ Soja           — cepea.org.br/br/indicador/soja.aspx
  ✅ Feijão         — cepea.org.br/br/indicador/feijao.aspx
  ✅ Arroz          — cepea.org.br/br/indicador/arroz.aspx
  ❌ Boi Gordo      — sem tabela de dados
  ❌ Sorgo          — sem tabela de dados
  ❌ Milheto        — sem tabela de dados
  ❌ Uva            — sem tabela de dados

Licença dos dados: CEPEA (CC BY-NC 4.0)
"""

FONTE_ID = 'e0cf35ee-344e-41bb-a84f-3b7198db79cd'

REGIAO_NACIONAL_ID = 'f6bb49e2-78db-4e2a-9668-11773cacd93c'  # Nacional
REGIAO_SP_ID       = '0aa3e7f9-ae3b-430a-81ec-a3c22106a3e5'  # São Paulo

PRODUTOS = {
    'cafe_arabica': 'b65effe8-94fb-4f73-8404-7bdeddb74565',
    'milho':        '553e75be-a732-4ff5-9b93-11bb8861114a',
    'trigo':        '01340329-fc80-4598-a94a-80e3fb7cf9dc',
    'soja':         'f1fe7635-add9-4a03-b542-a27a57848682',
    'feijao':       '334457f7-ceab-4e59-8ece-ae6a275d82f8',
    'arroz':        'db5c774a-15b9-4a7e-8d99-1a3384c56bfc',
}

CEPEA_CONFIG = [
    # ── Grãos (tabela padrão, col_data=0, col_valor=1) ──────
    {
        'nome':       'Cafe Arabica',
        'produto_id': PRODUTOS['cafe_arabica'],
        'regiao_id':  REGIAO_SP_ID,
        'url':        'https://cepea.org.br/br/indicador/cafe.aspx',
        'wait_css':   'table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,  # R$/sc 60kg
    },
    {
        'nome':       'Milho',
        'produto_id': PRODUTOS['milho'],
        'regiao_id':  REGIAO_SP_ID,
        'url':        'https://cepea.org.br/br/indicador/milho.aspx',
        'wait_css':   'table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,  # R$/sc 60kg
    },
    {
        'nome':       'Trigo',
        'produto_id': PRODUTOS['trigo'],
        'regiao_id':  REGIAO_SP_ID,
        'url':        'https://cepea.org.br/br/indicador/trigo.aspx',
        'wait_css':   'table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,  # R$/sc 60kg
    },
    {
        'nome':       'Soja',
        'produto_id': PRODUTOS['soja'],
        'regiao_id':  REGIAO_SP_ID,
        'url':        'https://cepea.org.br/br/indicador/soja.aspx',
        'wait_css':   'table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,  # R$/sc 60kg
    },
    # ── Feijão (col_valor=2 = R$/sc) ────────────────────────
    {
        'nome':       'Feijao Carioca',
        'produto_id': PRODUTOS['feijao'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'url':        'https://cepea.org.br/br/indicador/feijao.aspx',
        'wait_css':   'table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  2,  # R$/sc 60kg (col 1 = região, col 2 = valor)
    },
    # ── Arroz (tabela imagenet-table, col_valor=1) ───────────
    {
        'nome':       'Arroz em Casca',
        'produto_id': PRODUTOS['arroz'],
        'regiao_id':  REGIAO_NACIONAL_ID,
        'url':        'https://cepea.org.br/br/indicador/arroz.aspx',
        'wait_css':   '.imagenet-table tbody tr td',
        'tabela_idx': 0,
        'col_data':   0,
        'col_valor':  1,  # R$/sc 50kg
    },
]
