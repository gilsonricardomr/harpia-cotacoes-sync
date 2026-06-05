#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script unificado de sincronização → Supabase

Fontes e horários:
09h15 BRT → bcb + cafe_milho
10h17 BRT → soja_boi

Uso:
  python sincronizar.py --fonte bcb
  python sincronizar.py --fonte cafe_milho
  python sincronizar.py --fonte soja_boi
  python sincronizar.py          → todas as fontes
"""

import os, sys, re, time, argparse, traceback
from datetime import datetime, timedelta, date

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

BCB_FONTE_ID      = 'f64f3c6e-9bdd-4e82-a158-983733760d9a'
SELIC_PRODUTO_ID  = '02ce74c6-280d-421f-ab05-9a04fd729692'
IPCA_PRODUTO_ID   = '81719845-bca4-44ff-838d-11411c9136ed'

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# IDs dos produtos do Investing.com para filtrar por grupo
INVESTING_CAFE_MILHO = {
    'b65effe8-94fb-4f73-8404-7bdeddb74565',  # Café Arábica
    '553e75be-a732-4ff5-9b93-11bb8861114a',  # Milho
}
INVESTING_SOJA_BOI = {
    'f1fe7635-add9-4a03-b542-a27a57848682',  # Soja
    '9e382636-0b57-482b-a836-522da43b6228',  # Boi Gordo
}

INVESTING_SLEEP_RETRY   = 30
INVESTING_SLEEP_PRODUTO = 24


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
        print(f"  ❌ Erro cotações: {e}"); return 0, len(registros)


def upsert_indicadores(supabase, registros):
    if not registros: return 0, 0
    try:
        supabase.table('mercado_indicadores').upsert(
            registros, on_conflict='produto_id,data_cotacao,fonte_id').execute()
        return len(registros), 0
    except Exception as e:
        print(f"  ❌ Erro indicadores: {e}"); return 0, len(registros)


def limpar_precos_cotacoes(supabase, produto_id, fonte_id, regiao_id, data_inicio, data_fim):
    try:
        resp = (supabase.table('mercado_cotacoes')
                .update({'preco_brl': None, 'preco_usd': None})
                .eq('produto_id', produto_id)
                .eq('fonte_id', fonte_id)
                .eq('regiao_id', regiao_id)
                .gte('data_cotacao', data_inicio)
                .lte('data_cotacao', data_fim)
                .execute())
        n = len(resp.data) if resp.data else 0
        if n > 0: print(f"  🔄 {n} registros zerados (trigger vai recalcular)")
        return n
    except Exception as e:
        print(f"  ⚠️ Erro ao zerar preços: {e}"); return 0


# ── BCB ──────────────────────────────────────────────────────

def sincronizar_dolar(supabase, dias=1):
    print("\n" + "─"*60 + "\n💵 DÓLAR (BCB)\n" + "─"*60)
    try:
        r = supabase.table('mercado_produtos').select('id,nome') \
            .or_('nome.ilike.%dólar%,nome.ilike.%dolar%,nome.ilike.%USD%').limit(1).execute()
        if not r.data: raise Exception("Produto Dólar não encontrado")
        prod_id = r.data[0]['id']; print(f"  ✅ {r.data[0]['nome']}")
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
        print(f"  📊 {len(registros)} cotações")
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte':'Dólar BCB','inseridos':ok,'erros':err}
    except Exception as e:
        return {'fonte':'Dólar BCB','inseridos':0,'erros':1,'excecao':str(e)}


def sincronizar_selic(supabase, dias=1):
    print("\n" + "─"*60 + "\n📈 SELIC (BCB)\n" + "─"*60)
    try:
        hoje = datetime.now()
        resp = requests.get(
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados"
            f"?formato=json&dataInicial={(hoje-timedelta(days=dias)).strftime('%d/%m/%Y')}"
            f"&dataFinal={hoje.strftime('%d/%m/%Y')}", timeout=15)
        resp.raise_for_status(); dados = resp.json()
        print(f"  📊 {len(dados)} registros")
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
    print("\n" + "─"*60 + "\n📊 IPCA (BCB)\n" + "─"*60)
    try:
        hoje = datetime.now()
        resp = requests.get(
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados"
            f"?formato=json&dataInicial={(hoje-timedelta(days=max(dias,395))).strftime('%d/%m/%Y')}"
            f"&dataFinal={hoje.strftime('%d/%m/%Y')}", timeout=15)
        resp.raise_for_status(); dados = resp.json()
        print(f"  📊 {len(dados)} meses")
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
        print(f"  📊 {len(registros)} registros diários")
        ok, err = upsert_indicadores(supabase, registros)
        return {'fonte':'IPCA BCB','inseridos':ok,'erros':err}
    except Exception as e:
        return {'fonte':'IPCA BCB','inseridos':0,'erros':1,'excecao':str(e)}


def sincronizar_bcb(supabase, dias=1):
    """Agrupa Dólar + SELIC + IPCA numa única chamada."""
    print("\n" + "═"*60 + "\n🏦 BCB — INDICADORES\n" + "═"*60)
    resultados = []
    resultados.append(sincronizar_dolar(supabase, dias))
    resultados.append(sincronizar_selic(supabase, dias))
    resultados.append(sincronizar_ipca(supabase, dias))
    total_ok  = sum(r.get('inseridos',0) for r in resultados)
    total_err = sum(r.get('erros',0)     for r in resultados)
    return {'fonte':'BCB','inseridos':total_ok,'erros':total_err}


# ── Helpers Investing ─────────────────────────────────────────

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
                    (r'^(\d{2})/(\d{2})/(\d{4})$', lambda m:f"{m.group(3)}-{m.group(2)}-{m.group(1)}")]:
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


def _fetch_investing(url):
    try:
        from curl_cffi import requests as cf
    except ImportError:
        print("  ❌ curl_cffi não instalado"); return None

    for i in range(3):
        try:
            resp = cf.get(url, impersonate="chrome120", timeout=30,
                          headers={'Accept-Language':'pt-BR,pt;q=0.9','Referer':'https://br.investing.com/'})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text,'html.parser')
                titulo = (soup.find('title') or object()).__dict__.get('string','') or ''
                if 'Just a moment' in titulo or 'Attention Required' in titulo:
                    print(f"  ⚠️ Cloudflare ativo (tentativa {i+1}/3) — aguardando {INVESTING_SLEEP_RETRY}s")
                    time.sleep(INVESTING_SLEEP_RETRY); continue
                return soup
            else:
                print(f"  ⚠️ HTTP {resp.status_code} (tentativa {i+1}/3) — aguardando {INVESTING_SLEEP_RETRY}s")
                time.sleep(INVESTING_SLEEP_RETRY)
        except Exception as e:
            print(f"  ⚠️ Erro (tentativa {i+1}/3): {e}"); time.sleep(INVESTING_SLEEP_RETRY)
    return None


def _sincronizar_investing_grupo(supabase, grupo_ids: set, nome_grupo: str):
    """Sincroniza apenas os produtos cujo produto_id esteja em grupo_ids."""
    hoje     = date.today()
    data_ini = hoje.replace(day=1).isoformat()
    data_fim = hoje.isoformat()

    print("\n" + "═"*60 +
          f"\n📈 INVESTING.COM — {nome_grupo} [{data_ini} → {data_fim}]\n" + "═"*60)
    print(f"  ⏱️ Sleep entre produtos: {INVESTING_SLEEP_PRODUTO}s | entre tentativas: {INVESTING_SLEEP_RETRY}s")

    configs  = [c for c in SCRAPING_CONFIG if c['produto_id'] in grupo_ids]
    cotacoes = []

    for idx, cfg in enumerate(configs):
        print(f"\n  📊 {cfg['nome']}")
        if idx > 0:
            print(f"  ⏳ Aguardando {INVESTING_SLEEP_PRODUTO}s...")
            time.sleep(INVESTING_SLEEP_PRODUTO)
        try:
            soup = _fetch_investing(cfg['url_historico'])
            if not soup:
                print(f"  ❌ Falha ao obter página"); continue

            moeda = _detectar_moeda(soup)
            tab   = None
            for c in [soup.find('table',{'id':re.compile(r'curr_table|historicalTbl',re.I)}),
                      soup.find('table',class_=re.compile(r'freeze-column-w-1|historical',re.I))]:
                if c and c.find('tbody'): tab=c; break
            if not tab:
                for t in soup.find_all('table'):
                    if t.find('tbody') and len(t.find('tbody').find_all('tr')) > 3: tab=t; break

            if not tab:
                print(f"  ⚠️ Tabela histórica não encontrada"); continue

            limpar_precos_cotacoes(supabase, cfg['produto_id'], INVESTING_FONTE_ID,
                                   cfg['regiao_id'], data_ini, data_fim)
            count = 0
            for linha in tab.find('tbody').find_all('tr'):
                cols = linha.find_all('td')
                if len(cols) < 2: continue
                di = _converter_data(cols[0].get_text(strip=True))
                if not di or di < data_ini or di > data_fim: continue
                p = _limpar_numero(cols[1].get_text(strip=True))
                if p and p > 0:
                    reg = {'produto_id':cfg['produto_id'],'fonte_id':INVESTING_FONTE_ID,
                           'regiao_id':cfg['regiao_id'],'data_cotacao':di}
                    reg['preco_usd' if moeda=='USD' else 'preco_brl'] = p
                    cotacoes.append(reg); count += 1
            print(f"  ✅ {count} registros — moeda: {moeda}")
        except Exception as e:
            print(f"  ⚠️ {cfg['nome']}: {e}"); traceback.print_exc()

    ok, err = upsert_cotacoes(supabase, cotacoes)
    return {'fonte':f'Investing ({nome_grupo})','inseridos':ok,'erros':err}


def sincronizar_cafe_milho(supabase, dias=1):
    return _sincronizar_investing_grupo(supabase, INVESTING_CAFE_MILHO, 'Café + Milho')


def sincronizar_soja_boi(supabase, dias=1):
    return _sincronizar_investing_grupo(supabase, INVESTING_SOJA_BOI, 'Soja + Boi Gordo')


# ── Main ─────────────────────────────────────────────────────

FONTES = {
    'bcb':        sincronizar_bcb,
    'cafe_milho': sincronizar_cafe_milho,
    'soja_boi':   sincronizar_soja_boi,
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dias',  type=int, default=1)
    p.add_argument('--fonte', choices=list(FONTES.keys()), default=None)
    args = p.parse_args(); dias = max(1, args.dias)

    print("="*60)
    print("🌾 SINCRONIZAÇÃO COMPLETA → SUPABASE")
    print(f"  Período: {'dia atual' if dias==1 else f'últimos {dias} dias'}")
    print("="*60)

    try:
        supabase = conectar_supabase(); print("✅ Supabase conectado\n")
    except EnvironmentError as e:
        print(f"\n❌ {e}"); sys.exit(1)

    fontes     = {args.fonte: FONTES[args.fonte]} if args.fonte else FONTES
    resultados = []
    for nome, fn in fontes.items():
        try:
            resultados.append(fn(supabase=supabase, dias=dias))
        except Exception as e:
            print(f"\n❌ '{nome}': {e}"); traceback.print_exc()
            resultados.append({'fonte':nome,'inseridos':0,'erros':-1,'excecao':str(e)})

    print("\n" + "="*60 + "\n📋 RESULTADO FINAL\n" + "="*60)
    tok = terr = 0; ok_geral = True
    for r in resultados:
        ok = r.get('inseridos',0); err = r.get('erros',0)
        tok += ok; terr += err
        st   = "✅" if err==0 and not r.get('excecao') else "⚠️ " if ok>0 else "❌"
        linha = f"  {st} {r['fonte']:28} inseridos: {ok:4d}  erros: {err:4d}"
        if r.get('aviso'):   linha += f"  [{r['aviso']}]"
        if r.get('excecao'): linha += f"  [EXCEÇÃO]"; ok_geral = False
        if err > 0: ok_geral = False
        print(linha)
    print("─"*60)
    print(f"  {'TOTAL':30} inseridos: {tok:4d}  erros: {terr:4d}")
    print("="*60)
    print("\n🟢 CONCLUÍDO COM SUCESSO\n" if ok_geral else "\n🔴 CONCLUÍDO COM ERROS\n")
    sys.exit(0 if ok_geral else 1)


if __name__ == '__main__':
    main()
