import os
import time
import random
import requests
import schedule
import pytz
import re

from datetime import datetime

# ============================================================
# CONFIGURAÇÕES DA EVOLUTION API
# ============================================================

EVOLUTION_URL = os.environ.get(
    "EVOLUTION_URL",
    "https://evolution-api-production-1472.up.railway.app"
)

EVOLUTION_INSTANCE = "evolution-api-production-1472"

EVOLUTION_APIKEY = os.environ.get(
    "EVOLUTION_APIKEY",
    "SUA_API_KEY"
)

GRUPO_ID = os.environ.get(
    "GRUPO_ID",
    "556181595878-1598281026@g.us"
)

# ============================================================
# CONFIGURAÇÕES DE HORÁRIO
# ============================================================

HORA_INICIO = 8
HORA_FIM = 22
INTERVALO_HORAS = 2

FUSO_HORARIO = pytz.timezone("America/Sao_Paulo")

# ============================================================
# LINKS AFILIADOS
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

        return (
            f"{valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except:

        return "0,00"

# ============================================================
# EXTRAI ID MLB
# ============================================================

def extrair_id_produto(url):

    try:

        print(f"\n🔍 Resolvendo link: {url}")

        r = session.get(
            url,
            timeout=20,
            allow_redirects=True
        )

        final_url = r.url

        print(f"🌐 URL final: {final_url}")

        # ====================================================
        # PROCURA MLB123456789
        # ====================================================

        match = re.search(
            r'(MLB[-]?\d+)',
            final_url
        )

        if match:

            item_id = (
                match.group(1)
                .replace("-", "")
            )

            print(f"✅ ID encontrado URL: {item_id}")

            return item_id

        # ====================================================
        # PROCURA MLB NO HTML
        # ====================================================

        html = r.text

        match = re.search(
            r'(MLB[-]?\d+)',
            html
        )

        if match:

            item_id = (
                match.group(1)
                .replace("-", "")
            )

            print(f"✅ ID encontrado HTML: {item_id}")

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

    try:

        url = f"https://api.mercadolibre.com/items/{item_id}"

        print(f"📡 Consultando API: {item_id}")

        r = session.get(
            url,
            timeout=20
        )

        print(f"📶 Status API: {r.status_code}")

        if r.status_code != 200:

            print("❌ API retornou erro.")

            return None

        data = r.json()

        titulo = data.get("title")
        preco = data.get("price")
        preco_original = data.get("original_price")

        # ====================================================
        # IMAGEM PRINCIPAL
        # ====================================================

        imagem = ""

        pictures = data.get("pictures", [])

        if pictures and isinstance(pictures, list):

            imagem = pictures[0].get(
                "secure_url",
                ""
            )

        # FALLBACK
        if not imagem:

            imagem = data.get(
                "secure_thumbnail",
                ""
            )

        # ====================================================
        # FRETE
        # ====================================================

        shipping = data.get("shipping", {})

        frete_gratis = shipping.get(
            "free_shipping",
            False
        )

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

    preco_original = dados.get(
        "original_price"
    )

    desconto = 0

    if (
        preco_original
        and preco_original > preco
    ):

        desconto = round(
            (
                1 - (preco / preco_original)
            ) * 100
        )

    return {
        "titulo": dados.get(
            "title",
            "Produto"
        ),
        "preco": preco,
        "original": preco_original,
        "desconto": desconto,
        "frete": dados.get(
            "shipping",
            {}
        ).get(
            "free_shipping",
            False
        ),
        "imagem": dados.get(
            "thumbnail",
            ""
        ),
        "link": link_afiliado
    }

# ============================================================
# MONTA MENSAGEM
# ============================================================

def montar_mensagem(produto):

    texto = (
        f"🔥 *{produto['titulo']}*\n\n"
    )

    # PREÇO ORIGINAL
    if (
        produto["original"]
        and produto["original"] > produto["preco"]
    ):

        texto += (
            f"💸 De: "
            f"~R$ {formatar_preco(produto['original'])}~\n"
        )

    # PREÇO ATUAL
    texto += (
        f"💰 Por apenas: "
        f"*R$ {formatar_preco(produto['preco'])}*"
    )

    # DESCONTO
    if produto["desconto"] > 0:

        texto += (
            f" ({produto['desconto']}% OFF)"
        )

    # FRETE
    if produto["frete"]:

        texto += (
            "\n🚚 *Frete Grátis*"
        )

    # LINK
    texto += (
        f"\n\n🛒 *Comprar agora:*\n"
        f"{produto['link']}"
    )

    return texto

# ============================================================
# ENVIA WHATSAPP
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

            print("📤 Enviando imagem...")

            url = (
                f"{EVOLUTION_URL.rstrip('/')}"
                f"/message/sendMedia/"
                f"{EVOLUTION_INSTANCE}"
            )

            payload = {
                "number": GRUPO_ID,
                "mediatype": "image",
                "media": imagem,
                "caption": texto
            }

            r = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            print(
                f"📶 Status imagem: "
                f"{r.status_code}"
            )

            if r.status_code in [200, 201]:

                print(
                    "✅ Mensagem enviada "
                    "com imagem!"
                )

                return True

            print(
                f"⚠️ Falha imagem: "
                f"{r.text}"
            )

        except Exception as e:

            print(
                f"❌ Erro envio imagem: {e}"
            )

    # ========================================================
    # FALLBACK TEXTO
    # ========================================================

    try:

        print("📤 Enviando texto...")

        url = (
            f"{EVOLUTION_URL.rstrip('/')}"
            f"/message/sendText/"
            f"{EVOLUTION_INSTANCE}"
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

        print(
            f"📶 Status texto: "
            f"{r.status_code}"
        )

        if r.status_code in [200, 201]:

            print(
                "✅ Mensagem texto enviada!"
            )

            return True

        print(
            f"⚠️ Falha texto: "
            f"{r.text}"
            )

        return False

    except Exception as e:

        print(
            f"❌ Erro envio texto: {e}"
        )

        return False

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def executar():

    agora = obter_hora_local()

    # VERIFICA HORÁRIO
    if (
        agora.hour < HORA_INICIO
        or agora.hour >= HORA_FIM
    ):

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

    # ========================================================
    # EMBARALHA LINKS
    # ========================================================

    links_embaralhados = (
        LINKS_AFILIADOS.copy()
    )

    random.shuffle(
        links_embaralhados
    )

    produto = None

    # ========================================================
    # TESTA TODOS OS LINKS
    # ========================================================

    for link in links_embaralhados:

        print(
            f"\n🔎 Testando: {link}"
        )

        produto = buscar_oferta(link)

        if produto:

            print(
                "✅ Produto válido encontrado!"
            )

            break

        else:

            print(
                "⚠️ Link inválido."
            )

    # ========================================================
    # NENHUM LINK FUNCIONOU
    # ========================================================

    if not produto:

        print(
            "❌ Nenhum link válido encontrado."
        )

        return

    # ========================================================
    # EXIBE PRODUTO
    # ========================================================

    print(
        f"\n📦 {produto['titulo']}"
    )

    print(
        f"💰 R$ "
        f"{formatar_preco(produto['preco'])}"
    )

    mensagem = montar_mensagem(
        produto
    )

    # ========================================================
    # ENVIA WHATSAPP
    # ========================================================

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
        f"entre {HORA_INICIO}h "
        f"e {HORA_FIM}h"
    )

    # PRIMEIRA EXECUÇÃO
    executar()

    # AGENDAMENTO
    schedule.every(
        INTERVALO_HORAS
    ).hours.do(executar)

    # LOOP PRINCIPAL
    while True:

        try:

            schedule.run_pending()

            time.sleep(30)

        except KeyboardInterrupt:

            print(
                "\n🛑 Bot encerrado."
            )

            break

        except Exception as e:

            print(
                f"❌ Erro loop: {e}"
            )

            time.sleep(60)
