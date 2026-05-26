import os
import time
import random
import requests
import schedule
import pytz
import re
from datetime import datetime

# Configurações da Evolution API
EVOLUTION_URL      = os.environ.get("EVOLUTION_URL", "https://evolution-api-production-1472.up.railway.app")
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = os.environ.get("EVOLUTION_APIKEY", "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf")
GRUPO_ID           = os.environ.get("GRUPO_ID", "556181595878-1598281026@g.us")

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2
FUSO_HORARIO    = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

# ============================================================
# LISTA DE LINKS DE AFILIADO — adicione quantos quiser!
# ============================================================
LINKS_AFILIADOS = [
    "https://meli.la/2pD6jbV",
    "https://meli.la/2ue9rSS",
    "https://meli.la/1C6doSe",
    "https://meli.la/1o7cqys",
]

def extrair_id_produto(url):
    """Resolve o link curto e extrai o ID MLB do produto seguindo todos os redirecionamentos."""
    try:
        session = requests.Session()
        session.max_redirects = 10
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml"
        }

        # Segue todos os redirecionamentos e verifica cada URL
        resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)

        # Verifica todas as URLs do histórico de redirecionamentos
        urls_visitadas = [r.url for r in resp.history] + [resp.url]
        print(f"URLs visitadas: {len(urls_visitadas)}")

        for u in urls_visitadas:
            print(f"  → {u[:80]}")
            match = re.search(r'MLB-?(\d+)', u)
            if match:
                item_id = "MLB" + match.group(1)
                print(f"✅ ID encontrado: {item_id}")
                return item_id

        # Tenta extrair do conteúdo HTML da página
        html = resp.text
        match = re.search(r'MLB-?(\d{6,12})', html)
        if match:
            item_id = "MLB" + match.group(1)
            print(f"✅ ID encontrado no HTML: {item_id}")
            return item_id

        print(f"URL final: {resp.url}")
        return None

    except Exception as e:
        print(f"Erro ao resolver URL: {e}")
        return None

def buscar_detalhes_produto(item_id):
    """Busca detalhes do produto via scraping da página do ML."""
    import json as jsonlib

    url = f"https://www.mercadolivre.com.br/p/{item_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status página ML: {r.status_code}")

        if r.status_code != 200:
            # Tenta URL alternativa
            url2 = f"https://www.mercadolivre.com.br/produto/{item_id}"
            r = requests.get(url2, headers=headers, timeout=15)
            print(f"Status página alt: {r.status_code}")

        html = r.text

        # Extrai dados do JSON-LD
        if '"@type":"Product"' in html or '"@type": "Product"' in html:
            try:
                inicio = html.find('"@type":"Product"')
                if inicio == -1:
                    inicio = html.find('"@type": "Product"')
                bloco = html[max(0, inicio-200):inicio+2000]
                # Extrai nome
                nome = ""
                if '"name":"' in bloco:
                    nome = bloco.split('"name":"')[1].split('"')[0]
                # Extrai preço
                preco = 0
                if '"price":' in bloco:
                    preco_str = bloco.split('"price":')[1].split(',')[0].strip().strip('"')
                    try: preco = float(preco_str)
                    except: pass
                # Extrai imagem
                imagem = ""
                if '"image":"' in bloco:
                    imagem = bloco.split('"image":"')[1].split('"')[0]
                elif '"image":["' in bloco:
                    imagem = bloco.split('"image":["')[1].split('"')[0]

                if nome:
                    print(f"✅ Dados extraídos do JSON-LD: {nome[:50]}")
                    return {"title": nome, "price": preco, "original_price": None,
                            "thumbnail": imagem, "shipping": {"free_shipping": "Frete grátis" in html}}
            except Exception as e:
                print(f"Erro JSON-LD: {e}")

        # Extrai título diretamente do HTML
        titulo = ""
        if '<h1 class="ui-pdp-title">' in html:
            titulo = html.split('<h1 class="ui-pdp-title">')[1].split('</h1>')[0].strip()
        elif '<title>' in html:
            titulo = html.split('<title>')[1].split('</title>')[0].split('|')[0].strip()

        # Extrai preço
        preco = 0
        if '"price":' in html:
            try:
                trecho = html.split('"price":')[1][:20]
                preco = float(trecho.split(',')[0].strip())
            except: pass

        # Extrai imagem
        imagem = ""
        if 'https://http2.mlstatic.com' in html:
            try:
                imagem = 'https://http2.mlstatic.com' + html.split('https://http2.mlstatic.com')[1].split('"')[0]
            except: pass

        if titulo:
            print(f"✅ Dados extraídos do HTML: {titulo[:50]}")
            return {"title": titulo, "price": preco, "original_price": None,
                    "thumbnail": imagem, "shipping": {"free_shipping": "Frete grátis" in html}}

        print("❌ Não foi possível extrair dados da página.")
        return None

    except Exception as e:
        print(f"Erro scraping: {e}")
        return None

def buscar_oferta(link_afiliado):
    """Busca os dados do produto a partir do link de afiliado."""
    print(f"🔍 Resolvendo link: {link_afiliado}")
    item_id = extrair_id_produto(link_afiliado)

    if not item_id:
        print("❌ Não foi possível extrair o ID do produto.")
        return None

    print(f"📦 ID encontrado: {item_id}")
    dados = buscar_detalhes_produto(item_id)

    if not dados:
        return None

    titulo      = dados.get("title", "Produto")
    preco       = dados.get("price", 0)
    preco_orig  = dados.get("original_price") or preco
    frete       = dados.get("shipping", {}).get("free_shipping", False)
    imagem      = dados.get("thumbnail", "").replace("I.jpg", "O.jpg")

    desconto = 0
    if preco_orig and preco_orig > preco:
        desconto = round((1 - preco / preco_orig) * 100)

    return {
        "titulo":   titulo,
        "preco":    preco,
        "original": preco_orig,
        "desconto": desconto,
        "frete":    frete,
        "imagem":   imagem,
        "link":     link_afiliado
    }

def montar_mensagem(p):
    texto  = f"🔥 *{p['titulo']}*\n\n"
    if p["desconto"] > 0:
        texto += f"De: ~R$ {p['original']:.2f}~\n"
    texto += f"💰 Por Apenas: *R$ {p['preco']:.2f}*"
    if p["desconto"] > 0:
        texto += f" (*{p['desconto']}% OFF*)"
    if p["frete"]:
        texto += f"\n✅ *Frete Grátis*"
    texto += f"\n\n🛒 *Comprar agora:* {p['link']}"
    return texto

def enviar_whatsapp(texto, imagem):
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}

    # Tenta enviar com imagem
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendMedia/{EVOLUTION_INSTANCE}"
    body = {"number": GRUPO_ID, "mediatype": "image", "media": imagem, "caption": texto}

    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")

        if r.status_code in [200, 201]:
            print("✅ Mensagem com imagem enviada!")
            return

        # Fallback: envia só texto
        print("⚠️ Tentando enviar só texto...")
        url2 = f"{EVOLUTION_URL.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE}"
        body2 = {"number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}
        r2 = requests.post(url2, json=body2, headers=headers, timeout=15)
        print(f"Status texto: {r2.status_code}")
        if r2.status_code in [200, 201]:
            print("✅ Mensagem texto enviada!")

    except Exception as e:
        print(f"❌ Erro: {e}")

def executar():
    agora = obter_hora_local()
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:
        print(f"⏸ Fora do horário ({agora.hour}h BRT). Aguardando...")
        return

    print(f"\n🔍 Buscando oferta... ({agora.strftime('%d/%m/%Y %H:%M')})")

    link = random.choice(LINKS_AFILIADOS)
    produto = buscar_oferta(link)

    if not produto:
        print("❌ Não foi possível buscar o produto.")
        return

    print(f"📦 {produto['titulo']}")
    print(f"💰 R$ {produto['preco']:.2f}")

    texto  = montar_mensagem(produto)
    imagem = produto["imagem"]
    enviar_whatsapp(texto, imagem)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas ML iniciado!")
    print(f"📱 Grupo: {GRUPO_ID}")
    print(f"⏰ Envios a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")
    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
