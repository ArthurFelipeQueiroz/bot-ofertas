import os
import time
import random
import requests
import schedule
import feedparser
import pytz
import json
from datetime import datetime

# Configurações da Evolution API
EVOLUTION_URL      = os.environ.get("EVOLUTION_URL", "https://evolution-api-production-1472.up.railway.app")
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = os.environ.get("EVOLUTION_APIKEY", "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf")
GRUPO_ID           = os.environ.get("GRUPO_ID", "120363423796606784@g.us")

# =====================================================================
# CONFIGURAÇÕES DO MERCADO LIVRE AFILIADOS
# =====================================================================
ML_CLIENT_ID     = "3284935202043125"
ML_CLIENT_SECRET = "rD5lE6JcQuqRbYA5fnXuCm6OuPpv8Fpi"
ML_REDIRECT_URI  = "https://google.com"
ML_AFILIADO_ID   = "2726901932480871"

# Seu código gerado na barra do Google (Será usado uma vez para criar o tokens_ml.txt)
CODE_INICIAL     = "TG-6a15e0a97bcbb800016f74b4-584022277"

TOKEN_FILE       = "tokens_ml.txt"
HORA_INICIO      = 8
HORA_FIM         = 22
INTERVALO_HORAS  = 2
FUSO_HORARIO     = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

def obter_access_token():
    """Gerencia, valida e renova o Access Token do Mercado Livre automaticamente."""
    # 1. Se o arquivo com as chaves já existe, tenta usá-lo ou renová-lo
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                dados = json.load(f)
            
            # Valida se o token atual ainda funciona na API deles
            test_r = requests.get("https://mercadolibre.com", headers={"Authorization": f"Bearer {dados['access_token']}"})
            if test_r.status_code == 200:
                return dados["access_token"]
                
            # Se o token venceu, usa o refresh_token permanente para gerar um novo
            print("🔄 Access Token expirado. Gerando um novo com o Refresh Token...")
            url = "https://mercadolibre.com"
            payload = {
                "grant_type": "refresh_token",
                "client_id": ML_CLIENT_ID,
                "client_secret": ML_CLIENT_SECRET,
                "refresh_token": dados["refresh_token"]
            }
            r = requests.post(url, data=payload, timeout=10)
            if r.status_code == 200:
                novos_dados = r.json()
                with open(TOKEN_FILE, "w") as f:
                    json.dump(novos_dados, f)
                return novos_dados["access_token"]
        except Exception as e:
            print(f"⚠️ Falha ao ler arquivo de tokens: {e}")

    # 2. Primeira Execução: Usa o CODE_INICIAL (TG-) para dar o pontapé inicial
    if CODE_INICIAL and "COLOQUE_AQUI" not in CODE_INICIAL:
        print("🔑 Gerando o arquivo de chaves permanentes com o Code Inicial...")
        url = "https://mercadolibre.com"
        payload = {
            "grant_type": "authorization_code",
            "client_id": ML_CLIENT_ID,
            "client_secret": ML_CLIENT_SECRET,
            "code": CODE_INICIAL,
            "redirect_uri": ML_REDIRECT_URI
        }
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            dados = r.json()
            with open(TOKEN_FILE, "w") as f:
                json.dump(dados, f)
            print("✅ Arquivo 'tokens_ml.txt' criado com sucesso!")
            return dados["access_token"]
        else:
            print(f"❌ O Code Inicial (TG-) expirou ou é inválido: {r.status_code} - {r.text}")

    print("❌ Sem tokens válidos disponíveis para uso.")
    return None

def gerar_link_afiliado(link_original):
    """Envia o link do produto para a API e retorna com o seu ID de afiliado embutido."""
    token = obter_access_token()
    if not token:
        print("⚠️ Token ausente. Postando link convencional sem comissão.")
        return link_original

    url_api = "https://mercadolibre.com"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "url": link_original,
        "app_id": ML_AFILIADO_ID
    }
    try:
        response = requests.post(url_api, json=body, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return response.json().get("affiliate_url", link_original)
        else:
            print(f"⚠️ Erro ao carimbar link de comissão ({response.status_code}). Enviando link padrão.")
            return link_original
    except Exception as e:
        print(f"⚠️ Falha de comunicação com a API de Afiliados: {e}")
        return link_original

def buscar_oferta():
    # Feeds RSS corretos que buscam produtos reais em promoção nas categorias
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
                print("🔗 Gerando link personalizado de afiliado...")
                link_afiliado = gerar_link_afiliado(link_comum)
                return {"title": titulo, "link": link_afiliado}
        except Exception as e:
            print(f"⚠️ Erro ao ler o feed {nome}: {e}")
            continue

    # Sistema de reserva seguro
    link_reserva = "https://mercadolivre.com.br"
    return {
        "title": "Confira a lista completa de ofertas com até 40% OFF hoje!",
        "link": gerar_link_afiliado(link_reserva)
    }

def montar_mensagem(oferta):
    titulo = oferta.get("title")
    link   = oferta.get("link")
    return f"🔥 *{titulo}*\n\n🛒 *Aproveite aqui:* {link}"

def enviar_whatsapp(texto):
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendText"
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}
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
            body_v1 = {"number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}
            print(f"🔗 Tentando Rota v1: {url_v1}")
            r = requests.post(url_v1, json=body_v1, headers=headers, timeout=15)
            
        print(f"Status da API WhatsApp: {r.status_code}")
        if r.status_code in [200, 201]:
            print("✅ Sucesso! Mensagem de afiliado enviada para o WhatsApp.")
        else:
            print(f"❌ Falha no disparo da mensagem: {r.text[:300]}")
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
    enviar_whatsapp(texto)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas com Renovação OAuth Iniciado!")
    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
