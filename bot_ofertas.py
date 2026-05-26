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
    # CORREÇÃO DA ROTA: Na Evolution API v1/v2, o padrão correto é '/message/sendText'
    # Sem a instância no final da URL, ela vai no corpo do JSON ou como parâmetro.
    # Vamos testar o formato oficial mais comum das rotas da Evolution:
    url = f"{EVOLUTION_URL}/message/sendText"
    
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "instanceName": EVOLUTION_INSTANCE, # Adicionado explicitamente para APIs mais novas
        "number": GRUPO_ID,
        "text": texto,
        "delay": 1200,
        "linkPreview": True
    }
    
    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"Status da API: {r.status_code} | Resposta: {r.text}")
        
        # Se ainda der 404, tentamos a rota alternativa antiga da v1
        if r.status_code == 404:
            print("⚠️ Tentando rota alternativa v1...")
            url_alt = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
            # Algumas versões esperam apenas o number e text se a instância já está na URL
            body_alt = {"number": GRUPO_ID, "text": texto}
            r_alt = requests.post(url_alt, json=body_alt, headers=headers, timeout=15)
            print(f"Status Rota Alt: {r_alt.status_code} | Resposta: {r_alt.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão com a Evolution API: {e}")


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
