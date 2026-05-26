import os
import time
import random
import requests
import schedule
import feedparser
import pytz
from datetime import datetime

# Se você configurou a EVOLUTION_URL na aba "Variables" do Railway, o os.environ vai puxar de lá corretamente.
# Deixamos o link da sua API real como garantia caso as variáveis do painel falhem.
EVOLUTION_URL      = os.environ.get("EVOLUTION_URL", "https://evolution-api-production-1472.up.railway.app")
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = os.environ.get("EVOLUTION_APIKEY", "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf")
GRUPO_ID           = os.environ.get("GRUPO_ID", "120363423796606784@g.us")

# =====================================================================
# CONFIGURAÇÕES DO MERCADO LIVRE AFILIADOS
# =====================================================================
ML_AFILIADO_ID   = "2726901932480871"
ML_ACCESS_TOKEN  = "xYTuuOZsoixT69e6XUO8g0Zn3YH3v3n8"

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2
FUSO_HORARIO    = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

def gerar_link_afiliado(link_original):
    """
    Usa a API oficial do Mercado Livre para transformar um link comum
    em um link de afiliado que te gera comissões.
    """
    if not ML_ACCESS_TOKEN or "COLOQUE_AQUI" in ML_ACCESS_TOKEN:
        print("⚠️ Chave de afiliado não configurada. Usando link padrão.")
        return link_original

    # URL OFICIAL DA API DE AFILIADOS DO MERCADO LIVRE (Corrigido)
    url_api = "https://mercadolibre.com"
    
    headers = {
        "Authorization": f"Bearer {ML_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    body = {
        "url": link_original,
        "app_id": ML_AFILIADO_ID
    }
    
    try:
        response = requests.post(url_api, json=body, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            dados_link = response.json()
            return dados_link.get("affiliate_url", link_original)
        else:
            print(f"⚠️ Erro ao gerar link de comissão (Status {response.status_code}). Usando link comum.")
            return link_original
    except Exception as e:
        print(f"⚠️ Falha na conexão com a API do Mercado Livre: {e}")
        return link_original

def buscar_oferta():
    # FEEDS RSS REAIS DE PROMOÇÕES DO MERCADO LIVRE (Corrigido)
    feeds = [
        ("ML-Smartphones", "https://mercadolivre.com.br"),
        ("ML-Notebooks",   "https://mercadolivre.com.br"),
        ("ML-Eletronicos",  "https://mercadolivre.com.br")
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
                item = random.choice(feed.entries[:10])
                titulo = item.get("title", "Oferta imperdível")
                link_comum = item.get("link", "")
                
                print(f"🛒 Produto encontrado: {titulo}")
                print("🔗 Convertendo link para formato de Afiliado...")
                
                # Transforma o link normal no seu link de comissão
                link_afiliado = gerar_link_afiliado(link_comum)
                
                return {
                    "title": titulo,
                    "link": link_afiliado
                }
        except Exception as e:
            print(f"⚠️ Erro ao ler feed {nome}: {e}")
            continue

    # Sistema de reserva caso os feeds falhem
    link_reserva = "https://mercadolivre.com.br"
    return {
        "title": "Confira a lista completa de ofertas com até 40% OFF hoje!",
        "link": gerar_link_afiliado(link_reserva)
    }

def montar_mensagem(oferta):
    titulo = oferta.get("title")
    link   = oferta.get("link")
    
    texto  = f"🔥 *{titulo}*\n\n"
    texto += f"🛒 *Aproveite aqui:* {link}"
    return texto

def enviar_whatsapp(texto):
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendText"
    
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    
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
            print(f"❌ Erro retornado pela Evolution API: {r.text[:300]}")
            
    except Exception as e:
        print(f"❌ Erro de conexão externa: {e}")

def ejecutar():
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
    
    ejecutar()
    
    schedule.every(INTERVALO_HORAS).hours.do(ejecutar)
    while True:
        schedule.run_pending()
        time.sleep(30)
