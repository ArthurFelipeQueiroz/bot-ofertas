import requests
import schedule
import time
import random
import os
from datetime import datetime

EVOLUTION_URL      = "https://evolution-api-production-1472.up.railway.app"
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf"
GRUPO_ID           = os.environ.get("GRUPO_ID", "120363423796606784@g.us")

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2

def extrair_entre(texto, inicio, fim):
    try:
        return texto.split(inicio)[1].split(fim)[0].strip()
    except:
        return ""

def buscar_oferta():
    # Tenta vários formatos de RSS/feed
    feeds = [
        ("ML-smartphones", "https://lista.mercadolivre.com.br/eletronicos-audio-video/smartphones-celulares/_Discount_10-100_RSS"),
        ("ML-notebooks",   "https://lista.mercadolivre.com.br/informatica/notebooks-acessorios/notebooks/_Discount_10-100_RSS"),
        ("Amazon-eletro",  "https://www.amazon.com.br/gp/rss/bestsellers/electronics"),
        ("Amazon-casa",    "https://www.amazon.com.br/gp/rss/bestsellers/home"),
    ]

    random.shuffle(feeds)

    for nome, url in feeds:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=15)
            print(f"Feed {nome}: {r.status_code}")

            if r.status_code != 200:
                continue

            conteudo = r.text

            # Log primeiros 300 chars para debug
            print(f"Preview: {conteudo[:300]}")

            # Tenta <item> (RSS)
            if "<item>" in conteudo or "<item " in conteudo:
                itens = conteudo.split("<item>")[1:] or conteudo.split("<item ")[1:]
                print(f"📰 {len(itens)} itens RSS encontrados")
                if itens:
                    item = random.choice(itens[:20])
                    titulo = extrair_entre(item, "<title>", "</title>").replace("<![CDATA[","").replace("]]>","").strip()
                    link   = extrair_entre(item, "<link>", "</link>") or extrair_entre(item, "<guid>", "</guid>")
                    desc   = extrair_entre(item, "<description>", "</description>")
                    imagem = ""
                    if 'src="' in desc:
                        imagem = extrair_entre(desc, 'src="', '"')
                    if not imagem or not imagem.startswith("http"):
                        imagem = "https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.22/mercadolibre/logo__large_plus@2x.png"
                    return {"title": titulo, "link": link, "image": imagem}

            # Tenta <entry> (Atom)
            elif "<entry>" in conteudo:
                itens = conteudo.split("<entry>")[1:]
                print(f"📰 {len(itens)} itens Atom encontrados")
                if itens:
                    item = random.choice(itens[:20])
                    titulo = extrair_entre(item, "<title>", "</title>").replace("<![CDATA[","").replace("]]>","").strip()
                    link_tag = extrair_entre(item, '<link href="', '"')
                    link = link_tag or extrair_entre(item, "<id>", "</id>")
                    imagem = extrair_entre(item, '<img src="', '"') or "https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.22/mercadolibre/logo__large_plus@2x.png"
                    return {"title": titulo, "link": link, "image": imagem}

        except Exception as e:
            print(f"Erro {nome}: {e}")
            continue

    return None

def montar_mensagem(oferta):
    titulo = oferta.get("title", "Oferta imperdível")
    link   = oferta.get("link", "")
    imagem = oferta.get("image", "")

    texto  = f"🔥 *{titulo}*\n\n"
    texto += f"🛒 Ver oferta: {link}"
    return texto, imagem

def enviar_whatsapp(texto, imagem):
    url = f"{EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_APIKEY}
    body = {"number": GRUPO_ID, "mediatype": "image", "media": imagem, "caption": texto}
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
