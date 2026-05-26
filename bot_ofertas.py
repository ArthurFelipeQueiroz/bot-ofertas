import os
import time
import random
import requests
import schedule
import feedparser
import pytz
from datetime import datetime

# Configurações da Evolution API
EVOLUTION_URL      = "https://railway.app"
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = os.environ.get("EVOLUTION_APIKEY", "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf")
GRUPO_ID           = os.environ.get("GRUPO_ID", "120363423796606784@g.us")

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2
FUSO_HORARIO    = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

def buscar_oferta():
    # Usando feeds do G1 que são abertos e nunca bloqueiam servidores
    feeds = [
        ("G1-Tecnologia", "https://globo.com"),
        ("G1-Economia", "https://globo.com")
    ]
    
    random.shuffle(feeds)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for nome, url in feeds:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue

            # Parse direto da URL ou conteúdo
            feed = feedparser.parse(response.content)
            
            if feed.entries:
                item = random.choice(feed.entries[:10])
                titulo = item.get("title", "Oferta Especial do Dia")
                link = item.get("link", "https://mercadolivre.com.br")
                
                # Procura imagem nas tags do G1
                imagem = "https://mlstatic.com"
                if "links" in item:
                    for l in item.links:
                        if "image" in l.get("type", ""):
                            imagem = l.get("href")
                
                return {"title": titulo, "link": link, "image": imagem}
        except Exception as e:
            print(f"Erro no feed {nome}: {e}")
            continue

    # SISTEMA DE RESERVA (Se todos os sites bloquearem, ele gera um post para não quebrar)
    print("⚠️ Usando post do sistema de reserva para testes...")
    ofertas_reserva = [
        {"title": "Smartphone Samsung Galaxy S23 Ultra 256GB - Cupom Ativo!", "link": "https://mercadolivre.com.br", "image": "https://mlstatic.com"},
        {"title": "Notebook Gamer Dell G15 Intel Core i5 8GB 512GB SSD", "link": "https://mercadolivre.com.br", "image": "https://mlstatic.com"}
    ]
    return random.choice(ofertas_reserva)

def montar_mensagem(oferta):
    titulo = oferta.get("title", "Oferta imperdível")
    link   = oferta.get("link", "")
    return f"🔥 *{titulo}*\n\n🛒 Ver oferta: {link}"

def enviar_whatsapp(texto, imagem):
    url = f"{EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "number": GRUPO_ID,
        "mediatype": "image",
        "media": imagem,
        "caption": texto
    }
    
    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"Resposta da API (Status {r.status_code}): {r.text}")
    except Exception as e:
        print(f"❌ Erro de conexão com a API: {e}")

def executar():
    agora = obter_hora_local()
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:
        print(f"⏸ Fora do horário comercial ({agora.hour}h BRT). Aguardando...")
        return

    print(f"\n🔍 Buscando postagem... ({agora.strftime('%d/%m/%Y %H:%M')})")
    oferta = buscar_oferta()
    
    texto = montar_mensagem(oferta)
    imagem = oferta.get("image")
    print(f"📦 Postando no grupo: {oferta.get('title')}")
    enviar_whatsapp(texto, imagem)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas WhatsApp iniciado com sucesso!")
    print(f"📱 ID do Grupo alvo: {GRUPO_ID}")
    print(f"⏰ Janela de envios: {HORA_INICIO}h às {HORA_FIM}h (Horário de Brasília)\n")
    
    executar()
    
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
