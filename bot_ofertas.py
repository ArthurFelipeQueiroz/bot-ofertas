import os
import time
import random
import requests
import schedule
import pytz
from datetime import datetime

# Configurações da Evolution API
EVOLUTION_URL      = os.environ.get("EVOLUTION_URL", "https://evolution-api-production-1472.up.railway.app")
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = os.environ.get("EVOLUTION_APIKEY", "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf")
GRUPO_ID           = os.environ.get("GRUPO_ID", "556181595878-1598281026@g.us")

# ID de afiliado do Mercado Livre
ML_AFILIADO_ID = "2726901932480871"

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2
FUSO_HORARIO    = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

def gerar_link_afiliado(link):
    """Adiciona parâmetros de afiliado diretamente na URL."""
    separador = "&" if "?" in link else "?"
    return f"{link}{separador}matt_tool=bot_ofertas&matt_word=oferta&partner_id={ML_AFILIADO_ID}"

def buscar_oferta():
    """Retorna uma oferta com link de afiliado."""
    ofertas = [
        {"title": "🔥 Até 50% OFF em Smartphones — Ofertas do Dia!", "link": "https://www.mercadolivre.com.br/ofertas#deals-components-context"},
        {"title": "💻 Notebooks em Promoção — Melhores Preços!", "link": "https://www.mercadolivre.com.br/ofertas/notebooks"},
        {"title": "📺 Smart TVs com desconto imperdível hoje!", "link": "https://www.mercadolivre.com.br/ofertas/smart-tv"},
        {"title": "🎧 Fones Bluetooth — Ofertas com Frete Grátis!", "link": "https://www.mercadolivre.com.br/c/fone-de-ouvido"},
        {"title": "⌚ Smartwatches com até 40% OFF!", "link": "https://www.mercadolivre.com.br/c/smartwatch"},
        {"title": "🏠 Eletrodomésticos em Oferta — Não perca!", "link": "https://www.mercadolivre.com.br/ofertas/eletrodomesticos"},
        {"title": "📱 iPhones e Samsung com os melhores preços!", "link": "https://www.mercadolivre.com.br/ofertas/celulares"},
        {"title": "☕ Cafeteiras e Eletrodomésticos com desconto!", "link": "https://www.mercadolivre.com.br/c/cafeteira"},
        {"title": "🎮 Games e Consoles em Oferta!", "link": "https://www.mercadolivre.com.br/ofertas/games"},
        {"title": "👟 Tênis e Calçados com até 60% OFF!", "link": "https://www.mercadolivre.com.br/ofertas/calcados"},
    ]

    oferta = random.choice(ofertas)
    link_afiliado = gerar_link_afiliado(oferta["link"])
    print(f"🛒 Oferta: {oferta['title']}")
    print(f"🔗 Link afiliado gerado!")
    return {"title": oferta["title"], "link": link_afiliado}

def montar_mensagem(oferta):
    titulo = oferta.get("title")
    link   = oferta.get("link")
    texto  = f"{titulo}\n\n"
    texto += f"🛒 *Aproveite aqui:* {link}"
    return texto

def enviar_whatsapp(texto):
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}

    # Tenta rota v2
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendText"
    body = {"instanceName": EVOLUTION_INSTANCE, "number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}

    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)

        # Se v2 falhar, tenta v1
        if r.status_code == 404:
            url = f"{EVOLUTION_URL.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE}"
            body = {"number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}
            r = requests.post(url, json=body, headers=headers, timeout=15)

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
    print("🤖 Bot de Ofertas ML iniciado!")
    print(f"📱 Grupo: {GRUPO_ID}")
    print(f"⏰ Envios a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")
    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
