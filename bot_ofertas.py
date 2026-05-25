import requests
import schedule
import time
import random
import os
import xml.etree.ElementTree as ET
from datetime import datetime

EVOLUTION_URL      = "https://evolution-api-production-1472.up.railway.app"
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf"
GRUPO_ID           = os.environ.get("GRUPO_ID", "120363423796606784@g.us")

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2

# RSS públicos do Mercado Livre por categoria
FEEDS_ML = [
    "https://lista.mercadolivre.com.br/eletronicos-audio-video/smartphones-celulares/_Discount_10-100_RSS",
    "https://lista.mercadolivre.com.br/informatica/notebooks-acessorios/notebooks/_Discount_10-100_RSS",
    "https://lista.mercadolivre.com.br/eletrodomesticos/_Discount_10-100_RSS",
    "https://lista.mercadolivre.com.br/esportes-fitness/_Discount_10-100_RSS",
]

def buscar_oferta():
    feed_url = random.choice(FEEDS_ML)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(feed_url, headers=headers, timeout=15)
        print(f"Feed ML: {r.status_code}")

        if r.status_code != 200:
            return None

        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        print(f"📰 {len(items)} itens encontrados")

        if not items:
            return None

        item = random.choice(items[:20])
        titulo = item.findtext("title", "Oferta")
        link   = item.findtext("link", "")
        desc   = item.findtext("description", "")

        # Extrai imagem
        imagem = ""
        for tag in ["enclosure", "{http://search.yahoo.com/mrss/}thumbnail"]:
            el = item.find(tag)
            if el is not None:
                imagem = el.get("url", "")
                break

        if not imagem and 'src="' in desc:
            try:
                imagem = desc.split('src="')[1].split('"')[0]
            except:
                pass

        # Extrai preço do título se possível
        preco = ""
        if "R$" in titulo:
            try:
                preco = "R$" + titulo.split("R$")[1].split(" ")[0]
            except:
                pass

        return {
            "title": titulo,
            "link": link,
            "image": imagem,
            "preco": preco
        }

    except Exception as e:
        print(f"Erro feed: {e}")
        return None

def montar_mensagem(oferta):
    titulo = oferta.get("title", "Oferta imperdível")
    link   = oferta.get("link", "")
    imagem = oferta.get("image", "https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.22/mercadolibre/logo__large_plus@2x.png")
    preco  = oferta.get("preco", "")

    texto  = f"🔥 *{titulo}*\n\n"
    if preco:
        texto += f"💰 *{preco}*\n\n"
    texto += f"🛒 Ver oferta no Mercado Livre: {link}"

    return texto, imagem

def enviar_whatsapp(texto, imagem):
    url = f"{EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_APIKEY}
    body = {
        "number": GRUPO_ID,
        "mediatype": "image",
        "media": imagem,
        "caption": texto
    }
    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        if r.status_code in [200, 201]:
            print(f"✅ Mensagem enviada! ({datetime.now().strftime('%H:%M:%S')})")
        else:
            print(f"❌ Erro envio: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Erro conexão: {e}")

def executar():
    hora_atual = datetime.now().hour
    if hora_atual < HORA_INICIO or hora_atual >= HORA_FIM:
        print(f"⏸ Fora do horário ({hora_atual}h). Aguardando...")
        return

    print(f"\n🔍 Buscando oferta... ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
    oferta = buscar_oferta()
    if not oferta:
        print("❌ Nenhuma oferta encontrada.")
        return

    texto, imagem = montar_mensagem(oferta)
    print(f"📦 {oferta.get('title', '')}")
    enviar_whatsapp(texto, imagem)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas WhatsApp iniciado!")
    print(f"📱 Grupo: {GRUPO_ID}")
    print(f"⏰ Enviando a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")
    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(60)
