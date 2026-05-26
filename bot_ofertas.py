import os
import time
import random
import requests
import schedule
import feedparser
import pytz
from datetime import datetime

# Suas configurações da Evolution API (Mantenha igual ao seu painel)
EVOLUTION_URL      = os.environ.get("EVOLUTION_URL", "https://railway.app")
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = os.environ.get("EVOLUTION_APIKEY", "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf")
GRUPO_ID           = os.environ.get("GRUPO_ID", "120363423796606784@g.us")

# =====================================================================
# CONFIGURAÇÕES DO MERCADO LIVRE AFILIADOS
# Cole aqui os seus dados do Portal de Afiliados do Mercado Livre
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

    # Endpoint oficial do Mercado Livre para criação de links de afiliados
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
            # Retorna o link encurtado de afiliado (geralmente começa com mlclick ou ://mercadolivre.com)
            return dados_link.get("affiliate_url", link_original)
        else:
            print(f"⚠️ Erro ao gerar link de comissão (Status {response.status_code}). Usando link comum.")
            return link_original
    except Exception as e:
        print(f"⚠️ Falha na conexão com a API do Mercado Livre: {e}")
        return link_original

def buscar_oferta():
    # Feeds RSS públicos de descontos reais do Mercado Livre 
    # (Estes links mostram os produtos que estão na página de ofertas do site)
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

# MANTENHA O RESTANTE DO SEU CÓDIGO (montar_mensagem, enviar_whatsapp, executar, etc) IGUALZINHO!
