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
    """Busca detalhes do produto pela API do ML."""
    token = os.environ.get("ML_ACCESS_TOKEN", "APP_USR-3284935202043125-052615-6b8af8244d1406c3727b311eea529f7e-584022277")

    tentativas = [
        # Tenta com token no header
        {"url": f"https://api.mercadolibre.com/items/{item_id}", "headers": {"Authorization": f"Bearer {token}"}},
        # Tenta com token na URL
        {"url": f"https://api.mercadolibre.com/items/{item_id}?access_token={token}", "headers": {}},
        # Tenta sem autenticação
        {"url": f"https://api.mercadolibre.com/items/{item_id}", "headers": {}},
    ]

    for t in tentativas:
        try:
            r = requests.get(t["url"], headers=t["headers"], timeout=10)
            print(f"Status API ML: {r.status_code}")
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"Erro: {e}")
            continue

    print("❌ Todas as tentativas falharam.")
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
