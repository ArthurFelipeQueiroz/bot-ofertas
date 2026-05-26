import os
import time
import random
import requests
import schedule
import feedparser
import pytz
from datetime import datetime

# O link PRECISA começar com a sua instância específica e terminar com .up.railway.app
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
    # Feeds abertos do G1 (Tecnologia e Economia) - Não bloqueiam o Railway
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

            feed = feedparser.parse(response.content)
            
            if feed.entries:
                item = random.choice(feed.entries[:15])
                return {
                    "title": item.get("title", "Oferta imperdível"),
                    "link": item.get("link", "https://mercadolivre.com.br")
                }
        except Exception as e:
            print(f"⚠️ Erro ao ler feed {nome}: {e}")
            continue

    # Sistema de reserva caso os sites caiam
    return {
        "title": "Smartphone Samsung Galaxy S23 Ultra 256GB em Oferta!",
        "link": "https://mercadolivre.com.br"
    }

def montar_mensagem(oferta):
    titulo = oferta.get("title")
    link   = oferta.get("link")
    
    # Monta um texto limpo e bem formatado para o WhatsApp
    texto  = f"🔥 *{titulo}*\n\n"
    texto += f"🛒 *Aproveite aqui:* {link}"
    return texto

def enviar_whatsapp(texto):
    # Formato oficial da Evolution API v2: o endpoint termina apenas em /sendText
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendText"
    
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    
    # Na v2, passamos a instância dentro do JSON
    body = {
        "instanceName": EVOLUTION_INSTANCE,
        "number": GRUPO_ID,
        "text": texto,
        "delay": 200,
        "linkPreview": True
    }
    
    try:
        print(f"🔗 Tentando Rota v2: {url}")
        r = requests.post(url, json=body, headers=headers, timeout=15)
        
        # Se der 404 (Rota v2 não encontrada), tenta automaticamente a Rota antiga v1
        if r.status_code == 404:
            print("⚠️ Rota v2 deu 404. Tentando formato alternativo da v1...")
            url_v1 = f"{EVOLUTION_URL.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE}"
            body_v1 = {
                "number": GRUPO_ID,
                "text": texto,
                "delay": 200,
                "linkPreview": True
            }
            print(f"🔗 Tentando Rota v1: {url_v1}")
            r = requests.post(url_v1, json=body_v1, headers=headers, timeout=15)

        print(f"Status da API: {r.status_code}")
        if r.status_code in [200, 201]:
            print("✅ Sucesso! Mensagem enviada para o grupo do WhatsApp.")
        else:
            print(f"❌ Erro retornado pela Evolution API: {r.text[:300]}") # Exibe apenas o começo para não poluir o log
            
    except Exception as e:
        print(f"❌ Erro de conexão externa: {e}")

def executar():
    agora = obter_hora_local()
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:
        print(f"⏸ Fora do horário comercial ({agora.hour}h BRT). Aguardando...")
        return

    print(f"\n🔍 Buscando nova postagem... ({agora.strftime('%d/%m/%Y %H:%M')})")
    oferta = buscar_oferta()
    texto = montar_mensagem(oferta)
    
    print(f"📦 Enviando texto: {oferta.get('title')}")
    enviar_whatsapp(texto)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas em Texto iniciado!")
    print(f"📱 ID do Grupo: {GRUPO_ID}")
    print(f"⏰ Envios a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")
    
    # Executa imediatamente ao iniciar para testar
    executar()
    
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
