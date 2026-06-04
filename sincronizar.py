#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script unificado de sincronização → Supabase

Fontes:
  1. Dólar BCB          → mercado_indicadores
  2. SELIC BCB          → mercado_indicadores
  3. IPCA BCB           → mercado_indicadores
  4. Investing.com      → mercado_cotacoes  (Selenium)
  5. CEPEA/ESALQ        → mercado_cotacoes  (Selenium) — feijão, arroz
"""

import os, sys, re, time, argparse, traceback
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
from config_cepea     import FONTE_ID as CEPEA_FONTE_ID,    CEPEA_CONFIG

BCB_FONTE_ID     = 'f64f3c6e-9bdd-4e82-a158-983733760d9a'
SELIC_PRODUTO_ID = '02ce74c6-280d-421f-ab05-9a04fd729692'
IPCA_PRODUTO_ID  = '81719845-bca4-44ff-838d-11411c9136ed'

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

CHROME_BINARY_PATHS = [
    '/opt/hostedtoolcache/setup-chrome/chromium/stable/x64/chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
]


def conectar_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise EnvironmentError("Configure SUPABASE_URL e SUPABASE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_cotacoes(supabase, registros):
    if not registros: return 0, 0
    try:
        supabase.table('mercado_cotacoes').upsert(
            registros, on_conflict='produto_id,data_cotacao,fonte_id,regiao_id').execute()
        return len(registros), 0
    except Exception as e:
        print(f"   ❌ Erro cotações: {e}"); return 0, len(registros)

def upsert_indicadores(supabase, registros):
    if not registros: return 0, 0
    try:
        supabase.table('mercado_indicadores').upsert(
            registros, on_conflict='produto_id,data_cotacao,fonte_id').execute()
        return len(registros), 0
    except Exception as e:
        print(f"   ❌ Erro indicadores: {e}"); return 0, len(registros)


# ── BCB ──────────────────────────────────────────────────────

def sincronizar_dolar(supabase, dias=1):
    print("\n" + "─"*60 + "\n💵  DÓLAR (BCB)\n" + "─"*60)
    try:
        r = supabase.table('mercado_produtos').select('id,nome') \
            .or_('nome.ilike.%dólar%,nome.ilike.%dolar%,nome.ilike.%USD%').limit(1).execute()
        if not r.data: raise Exception("Produto Dólar não encontrado")
        prod_id = r.data[0]['id']; print(f"   ✅ {r.data[0]['nome']}")
        hoje = datetime.now()
        url = (f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
               f"CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
               f"?@dataInicial='{(hoje-timedelta(days=dias)).strftime('%m-%d-%Y')}'"
               f"&@dataFinalCotacao='{hoje.strftime('%m-%d-%Y')}'"
               f"&$top=100&$format=json&$select=cotacaoVenda,dataHoraCotacao")
        resp = requests.get(url, timeout=15); resp.raise_for_status()
        vistas, registros = set(), []
        for item in resp.json().get('value', []):
            d = item['dataHoraCotacao'][:10]
            if d not in vistas:
                vistas.add(d)
                registros.append({'produto_id':prod_id,'fonte_id':BCB_FONTE_ID,
                                   'valor':item['cotacaoVenda'],'data_cotacao':d})
        print(f"   📊 {len(registros)} cotações")
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte':'Dólar BCB','inseridos':ok,'erros':err}
    except Exception as e:
        return {'fonte':'Dólar BCB','inseridos':0,'erros':1,'excecao':str(e)}

def sincronizar_selic(supabase, dias=1):
    print("\n" + "─"*60 + "\n📈  SELIC (BCB)\n" + "─"*60)
    try:
        hoje = datetime.now()
        resp = requests.get(
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados"
            f"?formato=json&dataInicial={(hoje-timedelta(days=dias)).strftime('%d/%m/%Y')}"
            f"&dataFinal={hoje.strftime('%d/%m/%Y')}", timeout=15)
        resp.raise_for_status(); dados = resp.json()
        print(f"   📊 {len(dados)} registros")
        registros = []
        for item in dados:
            try:
                registros.append({'produto_id':SELIC_PRODUTO_ID,'fonte_id':BCB_FONTE_ID,
                    'valor':float(item['valor'].replace(',','.')),
                    'data_cotacao':datetime.strptime(item['data'],'%d/%m/%Y').strftime('%Y-%m-%d')})
            except: continue
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte':'SELIC BCB','inseridos':ok,'erros':err}
    except Exception as e:
        return {'fonte':'SELIC BCB','inseridos':0,'erros':1,'excecao':str(e)}

def sincronizar_ipca(supabase, dias=1):
    print("\n" + "─"*60 + "\n📊  IPCA (BCB)\n" + "─"*60)
    try:
        hoje = datetime.now()
        resp = requests.get(
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados"
            f"?formato=json&dataInicial={(hoje-timedelta(days=max(dias,395))).strftime('%d/%m/%Y')}"
            f"&dataFinal={hoje.strftime('%d/%m/%Y')}", timeout=15)
        resp.raise_for_status(); dados = resp.json()
        print(f"   📊 {len(dados)} meses")
        registros = []
        for item in dados:
            try:
                dr = datetime.strptime(item['data'],'%d/%m/%Y')
                v  = float(item['valor'].replace(',','.'))
                pm = dr.replace(month=dr.month+1,day=1) if dr.month<12 else dr.replace(year=dr.year+1,month=1,day=1)
                d  = dr
                while d < pm:
                    if d.date() <= hoje.date():
                        registros.append({'produto_id':IPCA_PRODUTO_ID,'fonte_id':BCB_FONTE_ID,
                                          'valor':v,'data_cotacao':d.strftime('%Y-%m-%d')})
                    d += timedelta(days=1)
            except: continue
        print(f"   📊 {len(registros)} registros diários")
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte':'IPCA BCB','inseridos':ok,'erros':err}
    except Exception as e:
        return {'fonte':'IPCA BCB','inseridos':0,'erros':1,'excecao':str(e)}


# ── Selenium ──────────────────────────────────────────────────

def _criar_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        opts = Options()
        for a in ['--headless','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
                  '--window-size=1920,1080','--lang=pt-BR','--disable-blink-features=AutomationControlled']:
            opts.add_argument(a)
        opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        for path in CHROME_BINARY_PATHS:
            if os.path.exists(path):
                opts.binary_location = path
                print(f"   🌐 Chrome: {path}")
                break

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)
    except Exception as e:
        print(f"   ❌ driver: {e}"); return None

def _limpar_numero(t):
    if not t: return None
    t = re.sub(r'[R$\s%]','',t).strip(); t = re.sub(r'[^\d.,]','',t)
    if not t: return None
    if ',' in t and '.' in t:
        t = t.replace('.','').replace(',','.') if t.index('.')<t.index(',') else t.replace(',','')
    elif ',' in t: t = t.replace(',','.')
    try: return float(t)
    except: return None

def _converter_data(t):
    if not t: return None
    t = t.strip()
    for pat, fn in [(r'^(\d{2})\.(\d{2})\.(\d{4})$', lambda m:f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
                    (r'^(\d{2})/(\d{2})/(\d{4})$',     lambda m:f"{m.group(3)}-{m.group(2)}-{m.group(1)}")]:
        m = re.match(pat,t)
        if m: return fn(m)
    meses = {'jan':'01','fev':'02','feb':'02','mar':'03','abr':'04','apr':'04','mai':'05','may':'05',
             'jun':'06','jul':'07','ago':'08','aug':'08','set':'09','sep':'09','out':'10','oct':'10',
             'nov':'11','dez':'12','dec':'12'}
    m = re.match(r'(\w+)\.?\s+(\d{1,2}),?\s+(\d{4})',t,re.I)
    if m:
        mes = meses.get(m.group(1).lower()[:3])
        if mes: return f"{m.group(3)}-{mes}-{m.group(2).zfill(2)}"
    m = re.match(r'^(\d{4}-\d{2}-\d{2})',t)
    if m: return m.group(1)
    return None

def _detectar_moeda(soup):
    for p in [r'[Mm]oeda\s+em\s+(BRL|USD|EUR)',r'Traded in\s+(BRL|USD|EUR)']:
        m = re.search(p,soup.get_text())
        if m: return m.group(1).upper()
    e = soup.find(attrs={'data-test':'base-currency-label'})
    if e and e.get_text(strip=True).upper() in ('BRL','USD','EUR'):
        return e.get_text(strip=True).upper()
    return 'BRL'

def _extrair_preco_investing(soup):
    """
    Tenta múltiplos seletores para extrair o preço do Investing.com.
    O site muda a estrutura com frequência.
    """
    seletores = [
        # Seletores modernos
        lambda s: s.find(attrs={'data-test': 'instrument-price-last'}),
        lambda s: s.find('div', attrs={'data-test': 'instrument-price-last'}),
        # Seletores por classe
        lambda s: s.find(class_=re.compile(r'text-5xl|last-price|instrument-price')),
        lambda s: s.find('span', class_=re.compile(r'text-\[|priceText')),
        # Seletores legados
        lambda s: s.find(id='last_last'),
        lambda s: s.find('span', id=re.compile(r'last')),
        # Qualquer número grande em destaque (heurística)
        lambda s: next((e for e in s.find_all(['span','div'])
                        if e.get('class') and any('text-' in c for c in e.get('class',[]))
                        and re.match(r'^[\d,.]+$', e.get_text(strip=True))), None),
    ]
    for fn in seletores:
        try:
            e = fn(soup)
            if e:
                txt = e.get_text(strip=True)
                v = _limpar_numero(txt)
                if v and v > 0:
                    return txt
        except: continue
    return None


# ── Investing.com ─────────────────────────────────────────────

def sincronizar_investing(supabase, dias=1):
    print("\n" + "─"*60 + f"\n📈  INVESTING.COM  [{'dia atual' if dias==1 else f'últimos {dias} dias'}]\n" + "─"*60)
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        return {'fonte':'Investing.com','inseridos':0,'erros':0,'aviso':'Selenium não instalado'}

    driver = _criar_driver()
    if not driver:
        return {'fonte':'Investing.com','inseridos':0,'erros':0,'aviso':'Falha no driver'}

    cotacoes = []
    try:
        for cfg in SCRAPING_CONFIG:
            print(f"\n   📊 {cfg['nome']}")
            try:
                if dias == 1:
                    driver.get(cfg['url_atual'])
                    # Aguarda qualquer sinal de preço na página
                    try:
                        WebDriverWait(driver,20).until(
                            EC.any_of(
                                EC.presence_of_element_located((By.CSS_SELECTOR,'[data-test="instrument-price-last"]')),
                                EC.presence_of_element_located((By.ID,'last_last')),
                                EC.presence_of_element_located((By.CSS_SELECTOR,'.text-5xl')),
                            ))
                    except: time.sleep(8)

                    soup  = BeautifulSoup(driver.page_source,'html.parser')
                    moeda = _detectar_moeda(soup)
                    ps    = _extrair_preco_investing(soup)

                    if ps:
                        p = _limpar_numero(ps)
                        if p and p > 0:
                            reg = {'produto_id':cfg['produto_id'],'fonte_id':INVESTING_FONTE_ID,
                                   'regiao_id':cfg['regiao_id'],'data_cotacao':datetime.now().strftime('%Y-%m-%d')}
                            reg['preco_usd' if moeda=='USD' else 'preco_brl'] = p
                            cotacoes.append(reg)
                            print(f"   ✅ {p} {moeda}")
                        else:
                            print(f"   ⚠️  Preço inválido: {ps}")
                    else:
                        # Debug: mostra título da página para detectar bloqueio Cloudflare
                        titulo = soup.find('title')
                        print(f"   ⚠️  Preço não encontrado — título: {titulo.text if titulo else 'sem título'}")
                else:
                    driver.get(cfg['url_historico'])
                    try: WebDriverWait(driver,20).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table tbody tr td')))
                    except: time.sleep(10)
                    soup  = BeautifulSoup(driver.page_source,'html.parser')
                    moeda = _detectar_moeda(soup)
                    tab = None
                    for c in [soup.find('table',{'id':re.compile(r'curr_table|historicalTbl',re.I)}),
                               soup.find('table',class_=re.compile(r'freeze-column-w-1|historical',re.I))]:
                        if c and c.find('tbody'): tab=c; break
                    if not tab:
                        for t in soup.find_all('table'):
                            if t.find('tbody') and len(t.find('tbody').find_all('tr'))>5: tab=t; break
                    if tab:
                        lim = datetime.now()-timedelta(days=dias)
                        count = 0
                        for linha in tab.find('tbody').find_all('tr'):
                            cols = linha.find_all('td')
                            if len(cols)<2: continue
                            di = _converter_data(cols[0].get_text(strip=True))
                            if not di or datetime.strptime(di,'%Y-%m-%d')<lim: break
                            p = _limpar_numero(cols[1].get_text(strip=True))
                            if p and p > 0:
                                reg = {'produto_id':cfg['produto_id'],'fonte_id':INVESTING_FONTE_ID,
                                       'regiao_id':cfg['regiao_id'],'data_cotacao':di}
                                reg['preco_usd' if moeda=='USD' else 'preco_brl'] = p
                                cotacoes.append(reg); count += 1
                        print(f"   ✅ {count} registros históricos")
                    else:
                        print(f"   ⚠️  Tabela histórica não encontrada")
            except Exception as e:
                print(f"   ⚠️  {cfg['nome']}: {e}")
            time.sleep(3)
    finally:
        driver.quit(); print("\n   🌐 Navegador fechado")

    ok, err = upsert_cotacoes(supabase, cotacoes)
    return {'fonte':'Investing.com','inseridos':ok,'erros':err}


# ── CEPEA/ESALQ ───────────────────────────────────────────────

def sincronizar_cepea(supabase, dias=1):
    print("\n" + "─"*60 + f"\n🌾  CEPEA/ESALQ  [{'dia atual' if dias==1 else f'últimos {dias} dias'}]\n" + "─"*60)

    driver = _criar_driver()
    if not driver:
        return {'fonte':'CEPEA/ESALQ','inseridos':0,'erros':0,'aviso':'Falha no driver'}

    def _parse_data_cepea(txt):
        txt = txt.strip()
        for sep in ['/', '-']:
            parts = txt.split(sep)
            if len(parts) == 3 and len(parts[2]) == 4:
                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        return None

    def _parse_valor_cepea(txt):
        txt = txt.strip().replace('.','').replace(',','.')
        try: return round(float(txt), 4)
        except: return None

    registros = []
    lim = (datetime.now() - timedelta(days=dias)).date()

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        for cfg in CEPEA_CONFIG:
            print(f"\n   📊 {cfg['nome']}")
            try:
                driver.get(cfg['url'])

                # Usa o seletor CSS específico de cada produto para aguardar a tabela
                wait_css = cfg.get('wait_css', 'table tbody tr td')
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_css))
                    )
                    print(f"   ✅ Tabela carregada ({wait_css})")
                except Exception:
                    print(f"   ⚠️  Timeout aguardando '{wait_css}' — tentando mesmo assim")

                soup    = BeautifulSoup(driver.page_source, 'html.parser')
                tabelas = soup.find_all('table')
                print(f"   📋 {len(tabelas)} tabelas encontradas")

                if cfg['tabela_idx'] >= len(tabelas):
                    print(f"   ⚠️  Tabela índice {cfg['tabela_idx']} não existe"); continue

                tab    = tabelas[cfg['tabela_idx']]
                linhas = tab.find('tbody').find_all('tr') if tab.find('tbody') else tab.find_all('tr')[1:]
                print(f"   📋 {len(linhas)} linhas na tabela")

                valores_dia = {}
                for linha in linhas:
                    cols = linha.find_all('td')
                    if len(cols) <= max(cfg['col_data'], cfg['col_valor']): continue
                    data_iso = _parse_data_cepea(cols[cfg['col_data']].get_text(strip=True))
                    valor    = _parse_valor_cepea(cols[cfg['col_valor']].get_text(strip=True))
                    if not data_iso or not valor: continue
                    try:
                        if datetime.strptime(data_iso,'%Y-%m-%d').date() < lim: continue
                    except: continue
                    valores_dia.setdefault(data_iso, []).append(valor)

                count = 0
                for data_iso, vals in sorted(valores_dia.items(), reverse=True):
                    registros.append({
                        'produto_id':   cfg['produto_id'],
                        'fonte_id':     CEPEA_FONTE_ID,
                        'regiao_id':    cfg['regiao_id'],
                        'data_cotacao': data_iso,
                        'preco_brl':    round(sum(vals)/len(vals), 4),
                    })
                    count += 1

                ultimo = round(list(valores_dia.values())[0][0], 2) if valores_dia else '—'
                print(f"   ✅ {count} datas — último: {ultimo} BRL")

            except Exception as e:
                print(f"   ⚠️  {cfg['nome']}: {e}")
                traceback.print_exc()
    finally:
        driver.quit(); print("\n   🌐 Navegador fechado")

    ok, err = upsert_cotacoes(supabase, registros)
    return {'fonte':'CEPEA/ESALQ','inseridos':ok,'erros':err}


# ── Main ─────────────────────────────────────────────────────

FONTES = {
    'dolar':     sincronizar_dolar,
    'selic':     sincronizar_selic,
    'ipca':      sincronizar_ipca,
    'investing': sincronizar_investing,
    'cepea':     sincronizar_cepea,
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dias',  type=int, default=1)
    p.add_argument('--fonte', choices=list(FONTES.keys()), default=None)
    args = p.parse_args(); dias = max(1, args.dias)

    print("="*60)
    print("🌾  SINCRONIZAÇÃO COMPLETA → SUPABASE")
    print(f"    Período: {'dia atual' if dias==1 else f'últimos {dias} dias'}")
    print("="*60)

    try:
        supabase = conectar_supabase(); print("✅ Supabase conectado\n")
    except EnvironmentError as e:
        print(f"\n❌ {e}"); sys.exit(1)

    fontes = {args.fonte: FONTES[args.fonte]} if args.fonte else FONTES
    resultados = []
    for nome, fn in fontes.items():
        try:
            resultados.append(fn(supabase=supabase, dias=dias))
        except Exception as e:
            print(f"\n❌ '{nome}': {e}"); traceback.print_exc()
            resultados.append({'fonte':nome,'inseridos':0,'erros':-1,'excecao':str(e)})

    print("\n" + "="*60 + "\n📋  RESULTADO FINAL\n" + "="*60)
    tok = terr = 0; ok_geral = True
    for r in resultados:
        ok = r.get('inseridos',0); err = r.get('erros',0)
        tok += ok; terr += err
        st = "✅" if err==0 and not r.get('excecao') else "⚠️ " if ok>0 else "❌"
        linha = f"  {st}  {r['fonte']:22}  inseridos: {ok:4d}  erros: {err:4d}"
        if r.get('aviso'):   linha += f"  [{r['aviso']}]"
        if r.get('excecao'): linha += f"  [EXCEÇÃO]"; ok_geral = False
        if err > 0: ok_geral = False
        print(linha)
    print("─"*60)
    print(f"  {'TOTAL':24}  inseridos: {tok:4d}  erros: {terr:4d}")
    print("="*60)
    print("\n🟢  CONCLUÍDO COM SUCESSO\n" if ok_geral else "\n🔴  CONCLUÍDO COM ERROS\n")
    sys.exit(0 if ok_geral else 1)

if __name__ == '__main__':
    main()
