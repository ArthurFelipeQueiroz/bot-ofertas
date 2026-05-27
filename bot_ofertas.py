import os
import time
import random
import requests
import schedule
import pytz
import re

from datetime import datetime

# ============================================================
# CONFIGURAÇÕES
# ============================================================

EVOLUTION_URL = os.environ.get(
    "EVOLUTION_URL",
    "https://evolution-api-production-1472.up.railway.app"
)

EVOLUTION_INSTANCE = os.environ.get(
    "EVOLUTION_INSTANCE",
    "evolution-api-production-1472"
)

EVOLUTION_APIKEY = os.environ.get(
    "EVOLUTION_APIKEY",
    "SUA_API_KEY"
)

GRUPO_ID = os.environ.get(
    "GRUPO_ID",
    "556181595878-1598281026@g.us"
)

HORA_INICIO = 8
HORA_FIM = 22
INTERVALO_HORAS = 2

FUSO_HORARIO = pytz.timezone("America/Sao_Paulo")

# ============================================================
# LINKS DE AFILIADO
# ============================================================

LINKS_AFILIADOS = [
    "https://meli.la/2pD6jbV",
    "https://meli.la/2ue9rSS",
    "https://meli.la/1C6doSe",
    "https://meli.la/1o7cqys",
]

# ============================================================
# SESSION GLOBAL
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "application/json,text/html,*/*"
})

# ============================================================
# UTILIDADES
# ============================================================

def obter_hora_local():
    return datetime.now(FUSO_HORARIO)


def formatar_preco(valor):
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"


# ============================================================
# EXTRAI ID MLB
# ============================================================

def extrair_id_produto(url):
    """
    Resolve o link afiliado e extrai o MLBXXXXXXXX.
    """

    try:
        print(f"\n🔍 Resolvendo link: {url}")

        r = session.get(
            url,
            timeout=20,
            allow_redirects=True
        )

        final_url = r.url

        print(f"🌐 URL final: {final_url}")

        # Procura MLB123456789
        match = re.search(r'(MLB\d+)', final_url)

        if match:
            item_id = match.group(1)

            print(f"✅ ID encontrado: {item_id}")

            return item_id

        # Procura MLB-123456789
        match = re.search(r'MLB-(\d+)', final_url)

        if match:
            item_id = f"MLB{match.group(1)}"

            print(f"✅ ID encontrado: {item_id}")

            return item_id

        print("❌ ID MLB não encontrado.")

        return None

    except Exception as e:
        print(f"❌ Erro ao resolver link: {e}")

        return None


# ============================================================
# API OFICIAL MERCADO LIVRE
# ============================================================

def buscar_detalhes_produto(item_id):
    """
    Busca dados oficiais via API do Mercado Livre.
    """

    try:
        url = f"https://api.mercadolibre.com/items/{item_id}"

        print(f"📡 Consultando API ML: {item_id}")

        r = session.get(url, timeout=20)

        print(f"📶 Status API: {r.status_code}")

        if r.status_code != 200:
            print("❌ API retornou erro.")
            return None

        data = r.json()

        titulo = data.get("title")
        preco = data.get("price")
        preco_original = data.get("original_price")

        # Imagem principal
        imagem = ""

        pictures = data.get("pictures", [])

        if pictures and isinstance(pictures, list):
            imagem = pictures[0].get("secure_url", "")

        # Fallback thumbnail
        if not imagem:
            imagem = data.get("secure_thumbnail", "")

        # Frete grátis
        shipping = data.get("shipping", {})
        frete_gratis = shipping.get("free_shipping", False)

        print(f"✅ Produto encontrado: {titulo}")

        return {
            "title": titulo,
            "price": preco,
            "original_price": preco_original,
            "thumbnail": imagem,
            "shipping": {
                "free_shipping": frete_gratis
            }
        }

    except Exception as e:
        print(f"❌ Erro API ML: {e}")

        return None


# ============================================================
# BUSCA OFERTA
# ============================================================

def buscar_oferta(link_afiliado):

    item_id = extrair_id_produto(link_afiliado)

    if not item_id:
        return None

    dados = buscar_detalhes_produto(item_id)

    if not dados:
        return None

    preco = dados.get("price") or 0
    preco_original = dados.get("original_price")

    desconto = 0

    if preco_original and preco_original > preco:
        desconto = round(
            (1 - (preco / preco_original)) * 100
        )

    return {
        "titulo": dados.get("title", "Produto"),
        "preco": preco,
        "original": preco_original,
        "desconto": desconto,
        "frete": dados.get("shipping", {}).get("free_shipping", False),
        "imagem": dados.get("thumbnail", ""),
        "link": link_afiliado
    }


# ============================================================
# MONTA MENSAGEM
# ============================================================

def montar_mensagem(produto):

    texto = f"🔥 *{produto['titulo']}*\n\n"

    # Preço antigo
    if (
        produto["original"]
        and produto["original"] > produto["preco"]
    ):
        texto += (
            f"💸 De: ~R$ {formatar_preco(produto['original'])}~\n"
        )

    # Preço atual
    texto += (
        f"💰 Por apenas: *R$ {formatar_preco(produto['preco'])}*"
    )

    # Desconto
    if produto["desconto"] > 0:
        texto += f" (*{produto['desconto']}% OFF*)"

    # Frete
    if produto["frete"]:
        texto += "\n🚚 *Frete Grátis*"

    texto += f"\n\n🛒 *Comprar agora:*\n{produto['link']}"

    return texto


# ============================================================
# ENVIO WHATSAPP
# ============================================================

def enviar_whatsapp(texto, imagem=None):

    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }

    # ========================================================
    # ENVIA COM IMAGEM
    # ========================================================

    if imagem:

        try:

            url = (
                f"{EVOLUTION_URL.rstrip('/')}"
                f"/message/sendMedia/{EVOLUTION_INSTANCE}"
            )

            payload = {
                "number": GRUPO_ID,
                "mediatype": "image",
                "media": imagem,
                "caption": texto
            }

            print("📤 Enviando mensagem com imagem...")

            r = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            print(f"📶 Status envio imagem: {r.status_code}")

            if r.status_code in [200, 201]:
                print("✅ Mensagem enviada com imagem!")
                return True

            print(f"⚠️ Falha envio imagem: {r.text}")

        except Exception as e:
            print(f"❌ Erro envio imagem: {e}")

    # ========================================================
    # FALLBACK TEXTO
    # ========================================================

    try:

        print("📤 Enviando fallback texto...")

        url = (
            f"{EVOLUTION_URL.rstrip('/')}"
            f"/message/sendText/{EVOLUTION_INSTANCE}"
        )

        payload = {
            "number": GRUPO_ID,
            "text": texto,
            "delay": 200,
            "linkPreview": True
        }

        r = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"📶 Status envio texto: {r.status_code}")

        if r.status_code in [200, 201]:
            print("✅ Mensagem texto enviada!")
            return True

        print(f"⚠️ Falha envio texto: {r.text}")

        return False

    except Exception as e:
        print(f"❌ Erro envio texto: {e}")

        return False


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def executar():

    agora = obter_hora_local()

    # Horário permitido
    if agora.hour < HORA_INICIO or agora.hour >= HORA_FIM:

        print(
            f"⏸ Fora do horário "
            f"({agora.strftime('%H:%M')})"
        )

        return

    print(
        f"\n=============================="
        f"\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}"
        f"\n=============================="
    )

    # Escolhe link aleatório
    link = random.choice(LINKS_AFILIADOS)

    produto = buscar_oferta(link)

    if not produto:
        print("❌ Não foi possível obter produto.")
        return

    print(f"\n📦 {produto['titulo']}")
    print(f"💰 R$ {formatar_preco(produto['preco'])}")

    mensagem = montar_mensagem(produto)

    enviar_whatsapp(
        texto=mensagem,
        imagem=produto["imagem"]
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n🤖 BOT MERCADO LIVRE INICIADO")
    print(f"📱 Grupo: {GRUPO_ID}")
    print(
        f"⏰ Envio a cada "
        f"{INTERVALO_HORAS}h "
        f"entre {HORA_INICIO}h e {HORA_FIM}h"
    )

    # Primeira execução imediata
    executar()

    # Agenda automática
    schedule.every(INTERVALO_HORAS).hours.do(executar)

    while True:

        try:
            schedule.run_pending()
            time.sleep(30)

        except KeyboardInterrupt:
            print("\n🛑 Bot encerrado manualmente.")
            break

        except Exception as e:
            print(f"❌ Erro no loop principal: {e}")
            time.sleep(60)
