import os
import time
import random
import requests
import schedule
import feedparser  # Adicionado para ler RSS de forma segura
import pytz        # Adicionado para corrigir o fuso horário no Railway
from datetime import datetime

# Configurações da Evolution API - RECOMENDÁVEL MOVER PARA VARIÁVEIS DE AMBIENTE
EVOLUTION_URL      = "https://evolution-api-production-1472.up.railway.app"
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
    feeds = [
        ("Tecnoblog-Ofertas", "https://tecnoblog.net"),
        ("Mundo-Conectado", "https://mundoconectado.com.br"),
    ]

    random.shuffle(feeds)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for nome, url in feeds:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"Feed {nome}: Status {response.status_code}")
            
            if response.status_code != 200:
                continue

            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                print(f"⚠️ Feed {nome} veio sem posts.")
                continue

            # Seleciona um post aleatório dos 15 mais recentes
            itens = feed.entries[:15]
            item = random.choice(itens)

            titulo = item.get("title", "Oferta imperdível")
            link = item.get("link", "")
            
            # Imagem padrão para o robô nunca quebrar caso não ache nenhuma no post
            imagem = "https://mlstatic.com"
            
            # 1. Tentativa via tags estruturadas do Feedparser
            if "media_content" in item and len(item.media_content) > 0:
                imagem = item.media_content[0]["url"]
            elif "links" in item:
                for l in item.links:
                    if "image" in l.get("type", ""):
                        imagem = l.get("href", imagem)
            
            # 2. Tentativa via HTML (Corrigido)
            if imagem == "https://mlstatic.com":
                conteudo_texto = item.get("description", "") + item.get("summary", "")
                if 'src="' in conteudo_texto:
                    try:
                        # Extrai corretamente o link entre as aspas do src
                        imagem = conteudo_texto.split('src="')[1].split('"')[0]
                    except Exception as e:
                        print(f"⚠️ Erro ao quebrar tag img: {e}")

            print(f"🎉 Encontrado: {titulo}")
            return {"title": titulo, "link": link, "image": imagem}

        except Exception as e:
            print(f"Erro ao processar o feed {nome}: {e}")
            continue

    return None

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
    
    # Payload adaptado para os padrões mais estáveis da Evolution API
    body = {
        "number": GRUPO_ID,
        "mediatype": "image",
        "media": imagem,       # Se não funcionar, mude a chave para "mediaUrl" dependendo da sua versão da API
        "caption": texto,
        "delay": 1200
    }
    
    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            print(f"✅ Mensagem enviada! ({obter_hora_local().strftime('%H:%M:%S')})")
        else:
            print(f"❌ Erro na Evolution API: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Erro de conexão com a API: {e}")

def executar():
    agora = obter_hora_local()
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:
        print(f"⏸ Fora do horário comercial ({agora.hour}h BRT). Aguardando...")
        return

    print(f"\n🔍 Buscando oferta... ({agora.strftime('%d/%m/%Y %H:%M')})")
    oferta = buscar_oferta()
    if not oferta:
        print("❌ Nenhuma oferta válida foi extraída dos feeds.")
        return

    texto = montar_mensagem(oferta)
    imagem = oferta.get("image")
    print(f"📦 Postando: {oferta.get('title')}")
    enviar_whatsapp(texto, imagem)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas WhatsApp iniciado com sucesso!")
    print(f"📱 ID do Grupo alvo: {GRUPO_ID}")
    print(f"⏰ Janela de envios: {HORA_INICIO}h às {HORA_FIM}h (Horário de Brasília)\n")
    
    # Executa uma vez na inicialização para testar
    executar()
    
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(30)
