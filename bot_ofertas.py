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
GRUPO_ID           = os.environ.get("GRUPO_ID", "556181595878-1598281026@g.us")

# Credenciais do Mercado Livre
ML_CLIENT_ID     = "3284935202043125"
ML_CLIENT_SECRET = "rD5lE6JcQuqRbYA5fnXuCm6OuPpv8Fpi"
ML_REDIRECT_URI  = "https://www.google.com"
ML_AFILIADO_ID   = "2726901932480871"
TOKEN_FILE       = "/tmp/tokens_ml.json"

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2
FUSO_HORARIO    = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

def salvar_tokens(dados):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(dados, f)
    except Exception as e:
        print(f"⚠️ Erro ao salvar tokens: {e}")

def obter_access_token():
    """Gerencia e renova o Access Token automaticamente."""

    # 1. Tenta usar tokens salvos no arquivo local
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                dados = json.load(f)
            access_token = dados.get("access_token")
            refresh_token = dados.get("refresh_token")

            # Testa se o token ainda é válido
            test = requests.get(
                "https://api.mercadolibre.com/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            if test.status_code == 200:
                print("✅ Token válido reutilizado!")
                return access_token

            # Token expirou, renova com refresh_token
            print("🔄 Renovando token via refresh_token...")
            r = requests.post("https://api.mercadolibre.com/oauth/token", data={
                "grant_type": "refresh_token",
                "client_id": ML_CLIENT_ID,
                "client_secret": ML_CLIENT_SECRET,
                "refresh_token": refresh_token
            }, timeout=10)

            if r.status_code == 200:
                novos = r.json()
                salvar_tokens(novos)
                print("✅ Token renovado com sucesso!")
                return novos["access_token"]
            else:
                print(f"⚠️ Erro ao renovar: {r.status_code}")

        except Exception as e:
            print(f"⚠️ Erro ao ler tokens locais: {e}")

    # 2. Usa tokens das variáveis do Railway
    access_token  = os.environ.get("ML_ACCESS_TOKEN", "")
    refresh_token = os.environ.get("ML_REFRESH_TOKEN", "")

    if access_token:
        print("📦 Usando token das variáveis do Railway...")
        salvar_tokens({"access_token": access_token, "refresh_token": refresh_token})
        return access_token

    print("❌ Nenhum token disponível.")
    return None

def gerar_link_afiliado(link_original):
    """Converte link comum em link de afiliado."""
    token = obter_access_token()
    if not token:
        return link_original

    try:
        r = requests.post(
            f"https://api.mercadolibre.com/users/{ML_AFILIADO_ID}/links",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"url": link_original},
            timeout=10
        )
        if r.status_code in [200, 201]:
            return r.json().get("affiliate_url", link_original)
        else:
            print(f"⚠️ Link afiliado erro ({r.status_code}): {r.text[:100]}")
            return link_original
    except Exception as e:
        print(f"⚠️ Erro ao gerar link: {e}")
        return link_original

def buscar_oferta():
    """Busca ofertas reais via sistema de reserva com links do ML."""
    ofertas = [
        {"title": "🔥 Até 50% OFF em Smartphones — Ofertas do Dia!", "link": "https://www.mercadolivre.com.br/ofertas#deals-components-context"},
        {"title": "💻 Notebooks em Promoção — Melhores Preços!", "link": "https://www.mercadolivre.com.br/ofertas/notebooks"},
        {"title": "📺 Smart TVs com desconto imperdível hoje!", "link": "https://www.mercadolivre.com.br/ofertas/smart-tv"},
        {"title": "🎧 Fones Bluetooth — Ofertas com Frete Grátis!", "link": "https://www.mercadolivre.com.br/ofertas/fone-bluetooth"},
        {"title": "⌚ Smartwatches e Relógios com até 40% OFF!", "link": "https://www.mercadolivre.com.br/ofertas/relogios"},
        {"title": "🏠 Eletrodomésticos em Oferta — Não perca!", "link": "https://www.mercadolivre.com.br/ofertas/eletrodomesticos"},
        {"title": "📱 iPhones e Samsung com os melhores preços!", "link": "https://www.mercadolivre.com.br/ofertas/celulares"},
        {"title": "☕ Cafeteiras e Eletrodomésticos de cozinha OFF!", "link": "https://www.mercadolivre.com.br/ofertas/cafeteiras"},
    ]

    oferta = random.choice(ofertas)
    print(f"🛒 Oferta selecionada: {oferta['title']}")

    # Converte para link de afiliado
    link_afiliado = gerar_link_afiliado(oferta["link"])
    return {"title": oferta["title"], "link": link_afiliado}

def montar_mensagem(oferta):
    titulo = oferta.get("title")
    link   = oferta.get("link")
    texto  = f"{titulo}\n\n"
    texto += f"🛒 *Aproveite aqui:* {link}"
    return texto

def enviar_whatsapp(texto):
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendText"
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}
    body = {"instanceName": EVOLUTION_INSTANCE, "number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}

    try:
        print(f"🔗 Tentando Rota v2: {url}")
        r = requests.post(url, json=body, headers=headers, timeout=15)

        if r.status_code == 404:
            print("⚠️ Tentando Rota v1...")
            url_v1 = f"{EVOLUTION_URL.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE}"
            body_v1 = {"number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}
            r = requests.post(url_v1, json=body_v1, headers=headers, timeout=15)

        print(f"Status WhatsApp: {r.status_code}")
        if r.status_code in [200, 201]:
            print("✅ Mensagem enviada com sucesso!")
        else:
            print(f"❌ Erro: {r.text[:200]}")

    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def executar():
    agora = obter_hora_local()
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:
        print(f"⏸ Fora do horário ({agora.hour}h BRT). Aguardando...")
        return

    print(f"\n🔍 Buscando oferta... ({agora.strftime('%d/%m/%Y %H:%M')})")
    oferta = buscar_oferta()
    texto  = montar_mensagem(oferta)
    enviar_whatsapp(texto)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas com Afiliado ML iniciado!")
    print(f"📱 Grupo: {GRUPO_ID}")
    print(f"⏰ Envios a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")

    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
