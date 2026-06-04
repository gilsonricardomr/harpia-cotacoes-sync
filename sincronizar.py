#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script unificado de sincronização → Supabase

Fontes:
  1. Dólar BCB          → mercado_indicadores  (PTAX venda)
  2. SELIC BCB          → mercado_indicadores  (série 432)
  3. IPCA BCB           → mercado_indicadores  (série 13522)
  4. Investing.com      → mercado_cotacoes     (Selenium)
  5. Yahoo Finance      → mercado_cotacoes     (yfinance)
  6. Alpha Vantage      → mercado_cotacoes     (API REST)

Todas as fontes rodam de forma independente.
Uma falha em qualquer fonte não interrompe as demais.

Uso:
  python sincronizar.py              → apenas o dia atual
  python sincronizar.py --dias 7    → últimos 7 dias
  python sincronizar.py --fonte dolar
  python sincronizar.py --fonte investing
  python sincronizar.py --fonte yahoo
  python sincronizar.py --fonte alpha
"""

import os
import sys
import re
import time
import argparse
import traceback
from datetime import datetime, timedelta

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client

from config_investing import FONTE_ID as INVESTING_FONTE_ID, SCRAPING_CONFIG
from config_yahoo import FONTE_ID as YAHOO_FONTE_ID, YAHOO_CONFIG
from config_alpha import FONTE_ID as ALPHA_FONTE_ID, ALPHA_CONFIG, BASE_URL as ALPHA_BASE_URL

# ============================================================
# CONSTANTES BCB
# ============================================================

BCB_FONTE_ID     = 'f64f3c6e-9bdd-4e82-a158-983733760d9a'
SELIC_PRODUTO_ID = '02ce74c6-280d-421f-ab05-9a04fd729692'
IPCA_PRODUTO_ID  = '81719845-bca4-44ff-838d-11411c9136ed'

# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY')


def conectar_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise EnvironmentError("Configure SUPABASE_URL e SUPABASE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_cotacoes(supabase: Client, registros: list) -> tuple:
    if not registros:
        return 0, 0
    try:
        supabase.table('mercado_cotacoes').upsert(
            registros, on_conflict='produto_id,data_cotacao,fonte_id,regiao_id'
        ).execute()
        return len(registros), 0
    except Exception as e:
        print(f"   ❌ Erro ao inserir cotações: {e}")
        return 0, len(registros)


def upsert_indicadores(supabase: Client, registros: list) -> tuple:
    if not registros:
        return 0, 0
    try:
        supabase.table('mercado_indicadores').upsert(
            registros, on_conflict='produto_id,data_cotacao,fonte_id'
        ).execute()
        return len(registros), 0
    except Exception as e:
        print(f"   ❌ Erro ao inserir indicadores: {e}")
        return 0, len(registros)


# ============================================================
# FONTE 1 — DÓLAR (BCB)
# ============================================================

def _obter_produto_dolar_id(supabase: Client) -> str:
    response = supabase.table('mercado_produtos') \
        .select('id, nome') \
        .or_('nome.ilike.%dólar%,nome.ilike.%dolar%,nome.ilike.%USD%') \
        .limit(1).execute()
    if not response.data:
        raise Exception("Produto Dólar não encontrado em mercado_produtos!")
    prod = response.data[0]
    print(f"   ✅ Produto: {prod['nome']} ({prod['id']})")
    return prod['id']


def sincronizar_dolar(supabase: Client, dias: int = 1) -> dict:
    print("\n" + "─" * 60)
    print("💵  DÓLAR (BCB)")
    print("─" * 60)
    try:
        produto_id = _obter_produto_dolar_id(supabase)
        hoje = datetime.now()
        data_fim    = hoje.strftime('%m-%d-%Y')
        data_inicio = (hoje - timedelta(days=dias)).strftime('%m-%d-%Y')
        url = (
            f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
            f"?@dataInicial='{data_inicio}'&@dataFinalCotacao='{data_fim}'"
            f"&$top=100&$format=json&$select=cotacaoVenda,dataHoraCotacao"
        )
        print(f"   📡 BCB PTAX: {data_inicio} → {data_fim}")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        dados = resp.json()
        datas_vistas: set = set()
        registros = []
        for item in dados.get('value', []):
            data = item['dataHoraCotacao'][:10]
            if data not in datas_vistas:
                datas_vistas.add(data)
                registros.append({'produto_id': produto_id, 'fonte_id': BCB_FONTE_ID,
                                   'valor': item['cotacaoVenda'], 'data_cotacao': data})
        print(f"   📊 {len(registros)} cotações encontradas")
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte': 'Dólar BCB', 'inseridos': ok, 'erros': err}
    except Exception as e:
        print(f"   ❌ {e}")
        return {'fonte': 'Dólar BCB', 'inseridos': 0, 'erros': 1, 'excecao': str(e)}


# ============================================================
# FONTE 2 — SELIC (BCB SGS série 432)
# ============================================================

def sincronizar_selic(supabase: Client, dias: int = 1) -> dict:
    print("\n" + "─" * 60)
    print("📈  SELIC (BCB)")
    print("─" * 60)
    try:
        hoje        = datetime.now()
        data_fim    = hoje.strftime('%d/%m/%Y')
        data_inicio = (hoje - timedelta(days=dias)).strftime('%d/%m/%Y')
        url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados"
               f"?formato=json&dataInicial={data_inicio}&dataFinal={data_fim}")
        print(f"   📡 BCB SGS série 432")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        dados = resp.json()
        print(f"   📊 {len(dados)} registros encontrados")
        registros = []
        for item in dados:
            try:
                data_iso = datetime.strptime(item['data'], '%d/%m/%Y').strftime('%Y-%m-%d')
                valor    = float(item['valor'].replace(',', '.'))
                registros.append({'produto_id': SELIC_PRODUTO_ID, 'fonte_id': BCB_FONTE_ID,
                                   'valor': valor, 'data_cotacao': data_iso})
            except Exception:
                continue
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte': 'SELIC BCB', 'inseridos': ok, 'erros': err}
    except Exception as e:
        print(f"   ❌ {e}")
        return {'fonte': 'SELIC BCB', 'inseridos': 0, 'erros': 1, 'excecao': str(e)}


# ============================================================
# FONTE 3 — IPCA (BCB SGS série 13522)
# ============================================================

def sincronizar_ipca(supabase: Client, dias: int = 1) -> dict:
    print("\n" + "─" * 60)
    print("📊  IPCA (BCB)")
    print("─" * 60)
    try:
        hoje       = datetime.now()
        data_fim   = hoje.strftime('%d/%m/%Y')
        dias_busca = max(dias, 395)
        data_inicio = (hoje - timedelta(days=dias_busca)).strftime('%d/%m/%Y')
        url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados"
               f"?formato=json&dataInicial={data_inicio}&dataFinal={data_fim}")
        print(f"   📡 BCB SGS série 13522")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        dados = resp.json()
        print(f"   📊 {len(dados)} meses encontrados")
        registros = []
        for item in dados:
            try:
                data_ref = datetime.strptime(item['data'], '%d/%m/%Y')
                valor    = float(item['valor'].replace(',', '.'))
                proximo_mes = (data_ref.replace(month=data_ref.month + 1, day=1)
                               if data_ref.month < 12
                               else data_ref.replace(year=data_ref.year + 1, month=1, day=1))
                dia_atual = data_ref
                while dia_atual < proximo_mes:
                    if dia_atual.date() <= hoje.date():
                        registros.append({'produto_id': IPCA_PRODUTO_ID, 'fonte_id': BCB_FONTE_ID,
                                          'valor': valor, 'data_cotacao': dia_atual.strftime('%Y-%m-%d')})
                    dia_atual += timedelta(days=1)
            except Exception:
                continue
        print(f"   📊 {len(registros)} registros diários")
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte': 'IPCA BCB', 'inseridos': ok, 'erros': err}
    except Exception as e:
        print(f"   ❌ {e}")
        return {'fonte': 'IPCA BCB', 'inseridos': 0, 'erros': 1, 'excecao': str(e)}


# ============================================================
# FONTE 4 — INVESTING.COM (Selenium)
# ============================================================

def _criar_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        for arg in ['--headless', '--no-sandbox', '--disable-dev-shm-usage',
                    '--disable-gpu', '--window-size=1920,1080', '--lang=pt-BR']:
            opts.add_argument(arg)
        opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        return webdriver.Chrome(options=opts)
    except Exception as e:
        print(f"   ❌ Erro ao criar driver: {e}")
        return None


def _limpar_numero(texto: str):
    if not texto:
        return None
    texto = re.sub(r'[R$\s%]', '', texto).strip()
    texto = re.sub(r'[^\d.,]', '', texto)
    if not texto:
        return None
    if ',' in texto and '.' in texto:
        texto = texto.replace('.', '').replace(',', '.') if texto.index('.') < texto.index(',') else texto.replace(',', '')
    elif ',' in texto:
        texto = texto.replace(',', '.')
    try:
        return float(texto)
    except ValueError:
        return None


def _converter_data(texto: str):
    if not texto:
        return None
    texto = texto.strip()
    m = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', texto)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', texto)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    meses = {'jan':'01','fev':'02','feb':'02','mar':'03','abr':'04','apr':'04',
             'mai':'05','may':'05','jun':'06','jul':'07','ago':'08','aug':'08',
             'set':'09','sep':'09','out':'10','oct':'10','nov':'11','dez':'12','dec':'12'}
    m = re.match(r'(\w+)\.?\s+(\d{1,2}),?\s+(\d{4})', texto, re.IGNORECASE)
    if m:
        mes = meses.get(m.group(1).lower()[:3])
        if mes:
            return f"{m.group(3)}-{mes}-{m.group(2).zfill(2)}"
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', texto)
    if m:
        return m.group(1)
    return None


def _detectar_moeda(soup) -> str:
    texto = soup.get_text()
    for padrao in [r'[Mm]oeda\s+em\s+(BRL|USD|EUR)', r'Traded in\s+(BRL|USD|EUR)']:
        m = re.search(padrao, texto)
        if m:
            return m.group(1).upper()
    elem = soup.find(attrs={'data-test': 'base-currency-label'})
    if elem:
        moeda = elem.get_text(strip=True).upper()
        if moeda in ('BRL', 'USD', 'EUR'):
            return moeda
    return 'BRL'


def _montar_registro_cotacao(config, preco, moeda, data) -> dict:
    reg = {'produto_id': config['produto_id'], 'fonte_id': INVESTING_FONTE_ID,
           'regiao_id': config['regiao_id'], 'data_cotacao': data}
    if moeda == 'USD':
        reg['preco_usd'] = preco
    else:
        reg['preco_brl'] = preco
    return reg


def sincronizar_investing(supabase: Client, dias: int = 1) -> dict:
    print("\n" + "─" * 60)
    print(f"📈  INVESTING.COM  [{'dia atual' if dias == 1 else f'últimos {dias} dias'}]")
    print("─" * 60)
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        return {'fonte': 'Investing.com', 'inseridos': 0, 'erros': 0,
                'aviso': 'Selenium não instalado'}

    driver = _criar_driver()
    if not driver:
        return {'fonte': 'Investing.com', 'inseridos': 0, 'erros': 0,
                'aviso': 'Falha ao iniciar o navegador'}

    todas_cotacoes = []
    try:
        for config in SCRAPING_CONFIG:
            print(f"\n   📊 {config['nome']}")
            try:
                if dias == 1:
                    url = config['url_atual']
                    driver.get(url)
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, '[data-test="instrument-price-last"]')))
                    except Exception:
                        time.sleep(7)
                    soup  = BeautifulSoup(driver.page_source, 'html.parser')
                    moeda = _detectar_moeda(soup)
                    preco_str = None
                    for sel in [
                        lambda s: s.find(attrs={'data-test': 'instrument-price-last'}),
                        lambda s: s.find(id='last_last'),
                        lambda s: s.find('span', class_=re.compile(r'text-5xl')),
                    ]:
                        elem = sel(soup)
                        if elem:
                            preco_str = elem.get_text(strip=True)
                            break
                    if preco_str:
                        preco = _limpar_numero(preco_str)
                        if preco and preco > 0:
                            data_hoje = datetime.now().strftime('%Y-%m-%d')
                            todas_cotacoes.append(
                                _montar_registro_cotacao(config, preco, moeda, data_hoje))
                else:
                    url = config['url_historico']
                    driver.get(url)
                    try:
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, 'table tbody tr td')))
                    except Exception:
                        time.sleep(10)
                    soup   = BeautifulSoup(driver.page_source, 'html.parser')
                    moeda  = _detectar_moeda(soup)
                    tabela = None
                    for candidato in [
                        soup.find('table', {'id': re.compile(r'curr_table|historicalTbl', re.I)}),
                        soup.find('table', class_=re.compile(r'freeze-column-w-1|historical', re.I)),
                    ]:
                        if candidato and candidato.find('tbody'):
                            tabela = candidato
                            break
                    if not tabela:
                        for t in soup.find_all('table'):
                            if t.find('tbody') and len(t.find('tbody').find_all('tr')) > 5:
                                tabela = t
                                break
                    if tabela:
                        data_limite = datetime.now() - timedelta(days=dias)
                        for linha in tabela.find('tbody').find_all('tr'):
                            cols = linha.find_all('td')
                            if len(cols) < 2:
                                continue
                            data_iso = _converter_data(cols[0].get_text(strip=True))
                            if not data_iso:
                                continue
                            if datetime.strptime(data_iso, '%Y-%m-%d') < data_limite:
                                break
                            preco = _limpar_numero(cols[1].get_text(strip=True))
                            if preco and preco > 0:
                                todas_cotacoes.append(
                                    _montar_registro_cotacao(config, preco, moeda, data_iso))
            except Exception as e:
                print(f"   ⚠️  Erro em {config['nome']}: {e}")
            time.sleep(3)
    finally:
        driver.quit()
        print("\n   🌐 Navegador fechado")

    ok, err = upsert_cotacoes(supabase, todas_cotacoes)
    return {'fonte': 'Investing.com', 'inseridos': ok, 'erros': err}


# ============================================================
# FONTE 5 — YAHOO FINANCE (yfinance)
# ============================================================

def sincronizar_yahoo(supabase: Client, dias: int = 1) -> dict:
    print("\n" + "─" * 60)
    print(f"📈  YAHOO FINANCE  [{'dia atual' if dias == 1 else f'últimos {dias} dias'}]")
    print("─" * 60)
    try:
        import yfinance as yf
    except ImportError:
        return {'fonte': 'Yahoo Finance', 'inseridos': 0, 'erros': 0,
                'aviso': 'yfinance não instalado (pip install yfinance)'}

    registros = []
    period = '1d' if dias == 1 else f'{dias}d'

    for config in YAHOO_CONFIG:
        print(f"   📊 {config['nome']} ({config['ticker']})")
        try:
            ticker = yf.Ticker(config['ticker'])
            hist   = ticker.history(period=period)
            if hist.empty:
                print(f"   ⚠️  Sem dados para {config['ticker']}")
                continue
            for data_idx, row in hist.iterrows():
                data_iso = data_idx.strftime('%Y-%m-%d')
                preco    = round(float(row['Close']), 4)
                reg = {
                    'produto_id':   config['produto_id'],
                    'fonte_id':     YAHOO_FONTE_ID,
                    'regiao_id':    config['regiao_id'],
                    'data_cotacao': data_iso,
                }
                if config['moeda'] == 'USD':
                    reg['preco_usd'] = preco
                else:
                    reg['preco_brl'] = preco
                registros.append(reg)
            print(f"   ✅ {len(hist)} registros")
        except Exception as e:
            print(f"   ⚠️  Erro em {config['nome']}: {e}")

    ok, err = upsert_cotacoes(supabase, registros)
    return {'fonte': 'Yahoo Finance', 'inseridos': ok, 'erros': err}


# ============================================================
# FONTE 6 — ALPHA VANTAGE (API REST)
# ============================================================

def sincronizar_alpha(supabase: Client, dias: int = 1) -> dict:
    print("\n" + "─" * 60)
    print(f"📈  ALPHA VANTAGE  [{'dia atual' if dias == 1 else f'últimos {dias} dias'}]")
    print("─" * 60)

    if not ALPHA_VANTAGE_KEY:
        return {'fonte': 'Alpha Vantage', 'inseridos': 0, 'erros': 0,
                'aviso': 'ALPHA_VANTAGE_KEY não configurada'}

    registros   = []
    data_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    for config in ALPHA_CONFIG:
        print(f"   📊 {config['nome']} ({config['function']})")
        try:
            params = {
                'function':   config['function'],
                'interval':   'daily',
                'datatype':   'json',
                'apikey':     ALPHA_VANTAGE_KEY,
            }
            resp = requests.get(ALPHA_BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            serie = data.get('data', [])
            if not serie:
                print(f"   ⚠️  Sem dados (resposta: {list(data.keys())})")
                continue

            count = 0
            for ponto in serie:
                data_iso = ponto.get('date', '')
                if data_iso < data_limite:
                    break
                valor = ponto.get('value', '')
                if not valor or valor == '.':
                    continue
                preco = round(float(valor), 4)
                reg = {
                    'produto_id':   config['produto_id'],
                    'fonte_id':     ALPHA_FONTE_ID,
                    'regiao_id':    config['regiao_id'],
                    'data_cotacao': data_iso,
                }
                if config['moeda'] == 'USD':
                    reg['preco_usd'] = preco
                else:
                    reg['preco_brl'] = preco
                registros.append(reg)
                count += 1

            print(f"   ✅ {count} registros")
            time.sleep(13)  # respeita limite de 5 req/min do plano free

        except Exception as e:
            print(f"   ⚠️  Erro em {config['nome']}: {e}")

    ok, err = upsert_cotacoes(supabase, registros)
    return {'fonte': 'Alpha Vantage', 'inseridos': ok, 'erros': err}


# ============================================================
# MAIN
# ============================================================

FONTES_DISPONIVEIS = {
    'dolar':     sincronizar_dolar,
    'selic':     sincronizar_selic,
    'ipca':      sincronizar_ipca,
    'investing': sincronizar_investing,
    'yahoo':     sincronizar_yahoo,
    'alpha':     sincronizar_alpha,
}


def main():
    parser = argparse.ArgumentParser(
        description='Sincroniza cotações de todas as fontes para o Supabase')
    parser.add_argument('--dias', type=int, default=1,
                        help='Dias retroativos (padrão: 1)')
    parser.add_argument('--fonte', choices=list(FONTES_DISPONIVEIS.keys()),
                        default=None, help='Executar apenas uma fonte específica')
    args = parser.parse_args()
    dias = max(1, args.dias)

    print("=" * 60)
    print("🌾  SINCRONIZAÇÃO COMPLETA → SUPABASE")
    print(f"    Período: {'dia atual' if dias == 1 else f'últimos {dias} dias'}")
    print("=" * 60)

    try:
        supabase = conectar_supabase()
        print("✅ Supabase conectado\n")
    except EnvironmentError as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)

    fontes = ({args.fonte: FONTES_DISPONIVEIS[args.fonte]}
              if args.fonte else FONTES_DISPONIVEIS)

    resultados = []
    for nome, fn in fontes.items():
        try:
            res = fn(supabase=supabase, dias=dias)
            resultados.append(res)
        except Exception as e:
            print(f"\n❌ Erro na fonte '{nome}': {e}")
            traceback.print_exc()
            resultados.append({'fonte': nome, 'inseridos': 0, 'erros': -1, 'excecao': str(e)})

    print("\n" + "=" * 60)
    print("📋  RESULTADO FINAL")
    print("=" * 60)
    total_ok = total_err = 0
    tudo_ok  = True
    for r in resultados:
        ok  = r.get('inseridos', 0)
        err = r.get('erros', 0)
        total_ok  += ok
        total_err += err
        status = "✅" if err == 0 and not r.get('excecao') else "⚠️ " if ok > 0 else "❌"
        linha  = f"  {status}  {r['fonte']:20}  inseridos: {ok:4d}  erros: {err:4d}"
        if r.get('aviso'):
            linha += f"  [{r['aviso']}]"
        if r.get('excecao'):
            linha += f"  [EXCEÇÃO: {r['excecao']}]"
            tudo_ok = False
        if err > 0:
            tudo_ok = False
        print(linha)
    print("─" * 60)
    print(f"  {'TOTAL':22}  inseridos: {total_ok:4d}  erros: {total_err:4d}")
    print("=" * 60)
    print("\n🟢  CONCLUÍDO COM SUCESSO\n" if tudo_ok else "\n🔴  CONCLUÍDO COM ERROS\n")
    sys.exit(0 if tudo_ok else 1)


if __name__ == '__main__':
    main()
