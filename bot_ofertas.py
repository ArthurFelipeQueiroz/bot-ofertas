def executar():

    agora = obter_hora_local()

    # Verifica horário permitido
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

    # ========================================================
    # EMBARALHA LINKS
    # ========================================================

    links_embaralhados = LINKS_AFILIADOS.copy()

    random.shuffle(links_embaralhados)

    produto = None

    # ========================================================
    # TESTA TODOS OS LINKS ATÉ ACHAR UM VÁLIDO
    # ========================================================

    for link in links_embaralhados:

        print(f"\n🔎 Testando link: {link}")

        produto = buscar_oferta(link)

        if produto:

            print("✅ Produto válido encontrado!")

            break

        else:

            print("⚠️ Link inválido, tentando próximo...")

    # ========================================================
    # NENHUM LINK FUNCIONOU
    # ========================================================

    if not produto:

        print("❌ Nenhum link válido encontrado.")

        return

    # ========================================================
    # EXIBE PRODUTO
    # ========================================================

    print(f"\n📦 {produto['titulo']}")
    print(f"💰 R$ {formatar_preco(produto['preco'])}")

    mensagem = montar_mensagem(produto)

    # ========================================================
    # ENVIA WHATSAPP
    # ========================================================

    enviar_whatsapp(
        texto=mensagem,
        imagem=produto["imagem"]
    )
