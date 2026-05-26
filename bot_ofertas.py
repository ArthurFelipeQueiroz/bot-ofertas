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

HORA_INICIO     = 8
HORA_FIM        = 22
INTERVALO_HORAS = 2
FUSO_HORARIO    = pytz.timezone("America/Sao_Paulo")

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)

# ============================================================
# LISTA DE PRODUTOS — adicione quantos quiser!
# ============================================================
PRODUTOS = [
    {
        "titulo":   "Perfume Club De Nuit Intense Da Armaf Edt 105ml Masculino",
        "preco":    "R$ 217,30",
        "original": "R$ 265,00",
        "desconto": "18% OFF no Pix",
        "frete":    True,
        "link":     "https://meli.la/1o7cqys",
        "imagem":   "https://http2.mlstatic.com/D_NQ_NP_2X_887864-MLB108264754941_032026-F.webp"
    },
]

def buscar_oferta():
    return random.choice(PRODUTOS)

def montar_mensagem(p):
    texto  = f"🔥 *{p['titulo']}*\n\n"
    texto += f"De: ~{p['original']}~\n"
    texto += f"💰 Por Apenas: *{p['preco']}*"
    if p.get("desconto"):
        texto += f" (*{p['desconto']}*)"
    if p.get("frete"):
        texto += f"\n✅ *Frete Grátis*"
    texto += f"\n\n🛒 *Comprar agora:* {p['link']}"
    return texto

def enviar_whatsapp(texto, imagem):
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}

    # Tenta enviar com imagem (v1)
    url = f"{EVOLUTION_URL.rstrip('/')}/message/sendMedia/{EVOLUTION_INSTANCE}"
    body = {
        "number":    GRUPO_ID,
        "mediatype": "image",
        "media":     imagem,
        "caption":   texto
    }

    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"Status WhatsApp: {r.status_code}")

        if r.status_code in [200, 201]:
            print("✅ Mensagem com imagem enviada!")
            return

        # Se falhar, envia só texto
        print("⚠️ Falha na imagem, enviando só texto...")
        url_txt = f"{EVOLUTION_URL.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE}"
        body_txt = {"number": GRUPO_ID, "text": texto, "delay": 200, "linkPreview": True}
        r2 = requests.post(url_txt, json=body_txt, headers=headers, timeout=15)
        print(f"Status texto: {r2.status_code}")
        if r2.status_code in [200, 201]:
            print("✅ Mensagem texto enviada!")
        else:
            print(f"❌ Erro: {r2.text[:200]}")

    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def executar():
    agora = obter_hora_local()
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:
        print(f"⏸ Fora do horário ({agora.hour}h BRT). Aguardando...")
        return

    print(f"\n🔍 Buscando oferta... ({agora.strftime('%d/%m/%Y %H:%M')})")
    produto = buscar_oferta()
    texto   = montar_mensagem(produto)
    imagem  = produto["imagem"]
    print(f"📦 {produto['titulo']}")
    enviar_whatsapp(texto, imagem)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas ML iniciado!")
    print(f"📱 Grupo: {GRUPO_ID}")
    print(f"⏰ Envios a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")
    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
