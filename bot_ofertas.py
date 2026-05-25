import requests
import schedule
import time
import random
from datetime import datetime

ML_APP_ID  = "557749699288936"
ML_SECRET  = "02WHbfviPxhjMMGKgRs8Ab78Laj2X5K8"

EVOLUTION_URL      = "https://evolution-api-production-1472.up.railway.app"
EVOLUTION_INSTANCE = "evolution-api-production-1472"
EVOLUTION_APIKEY   = "d9205c8f52a108765dfb5ae9039f10f5ac2f6eac17952a521a220d50ee997daf"

GRUPO_ID = "ID_DO_GRUPO@g.us"  # ← substitua pelo ID do seu grupo

HORA_INICIO = 8
HORA_FIM    = 22
INTERVALO_HORAS = 2

def obter_token():
    url = "https://api.mercadolibre.com/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": ML_APP_ID,
        "client_secret": ML_SECRET
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        token = r.json().get("access_token")
        print("✅ Token obtido!" if token else f"❌ Erro token: {r.json()}")
        return token
    except Exception as e:
        print(f"Erro token: {e}")
        return None

def buscar_produto(token):
    buscas = [
        "smartphone", "notebook", "smart tv",
        "airfryer", "perfume", "relogio",
        "iphone", "samsung", "aspirador", "cafeteira"
    ]
    busca = random.choice(buscas)
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={busca}&sort=relevance&limit=50&access_token={token}"

    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        results = data.get("results", [])
        print(f"🔎 '{busca}' — {len(results)} resultados")

        if not results:
            return None

        com_desconto = [
            p for p in results
            if p.get("original_price") and p["original_price"] > p["price"]
            and p.get("thumbnail")
        ]
        lista = com_desconto if com_desconto else [p for p in results if p.get("thumbnail")]
        return random.choice(lista) if lista else None

    except Exception as e:
        print(f"Erro busca: {e}")
        return None

def montar_mensagem(produto):
    nome        = produto.get("title", "Produto")
    preco_atual = produto.get("price", 0)
    preco_orig  = produto.get("original_price") or preco_atual
    imagem      = produto.get("thumbnail", "").replace("I.jpg", "O.jpg")
    link        = produto.get("permalink", "")

    desconto = 0
    if preco_orig and preco_orig > preco_atual:
        desconto = round((1 - preco_atual / preco_orig) * 100)

    texto = f"🔥 *{nome}*\n\n"
    if desconto > 0:
        texto += f"De: R$ {preco_orig:.2f}\n"
    texto += f"💰 Por Apenas: *R$ {preco_atual:.2f}*"
    if desconto > 0:
        texto += f" (*{desconto}% OFF*)"
    if produto.get("shipping", {}).get("free_shipping"):
        texto += "\n✅ *Frete Grátis*"
    texto += f"\n\n🛒 Comprar agora: {link}"

    return texto, imagem

def enviar_whatsapp(texto, imagem):
    url = f"{EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_APIKEY}
    body = {
        "number": GRUPO_ID,
        "mediatype": "image",
        "media": imagem,
        "caption": texto
    }
    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        if r.status_code in [200, 201]:
            print(f"✅ Mensagem enviada! ({datetime.now().strftime('%H:%M:%S')})")
        else:
            print(f"❌ Erro envio: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Erro conexão: {e}")

def executar():
    hora_atual = datetime.now().hour
    if hora_atual < HORA_INICIO or hora_atual >= HORA_FIM:
        print(f"⏸ Fora do horário ({hora_atual}h). Aguardando...")
        return

    print(f"\n🔍 Buscando oferta... ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
    token = obter_token()
    if not token:
        return

    produto = buscar_produto(token)
    if not produto:
        print("❌ Nenhum produto encontrado.")
        return

    texto, imagem = montar_mensagem(produto)
    print(f"📦 {produto.get('title', '')}")
    print(f"💰 R$ {produto.get('price', 0):.2f}")
    enviar_whatsapp(texto, imagem)

if __name__ == "__main__":
    print("🤖 Bot de Ofertas WhatsApp iniciado!")
    print(f"⏰ Enviando a cada {INTERVALO_HORAS}h entre {HORA_INICIO}h e {HORA_FIM}h\n")
    executar()
    schedule.every(INTERVALO_HORAS).hours.do(executar)
    while True:
        schedule.run_pending()
        time.sleep(60)
