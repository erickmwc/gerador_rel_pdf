import os
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from nicegui import ui
import threading
import asyncio

# Função para redimensionar a imagem mantendo a proporção e alta qualidade
def redimensionar_imagem(caminho_imagem, largura_max=900, altura_max=900):
    with Image.open(caminho_imagem) as img:
        if img.width > largura_max or img.height > altura_max:
            proporcao = min(largura_max / img.width, altura_max / img.height)
            novo_tamanho = (int(img.width * proporcao), int(img.height * proporcao))
            img = img.resize(novo_tamanho, Image.LANCZOS)  # Redimensiona com alta qualidade
        return img
    

# Função para desenhar o cabeçalho
def desenhar_cabecalho(c, largura_pagina, altura_pagina, caminho_imagem_cabecalho=None):
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura_pagina / 2, altura_pagina - 30, "Relatório Fotográfico")
    if caminho_imagem_cabecalho:
        c.drawImage(caminho_imagem_cabecalho, 10, altura_pagina - 70, width=550, height=70)

# Função para gerar o relatório PDF
def gerar_relatorio_pdf(titulo_principal, grupos_fotos):
    nome_pdf = f"uploads/relatorio_fotografico.pdf"
    caminho_imagem_cabecalho = "LogoCodevasf.png"  # Caminho da imagem do cabeçalho
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    largura_pagina, altura_pagina = A4

    # Desenhar o cabeçalho na primeira página
    desenhar_cabecalho(c, largura_pagina, altura_pagina, caminho_imagem_cabecalho)
    y_pos = altura_pagina - 110  # Ajustar a posição do conteúdo abaixo do cabeçalho

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura_pagina / 2, y_pos, titulo_principal)
    y_pos -= 30

    for grupo in grupos_fotos:
        titulo_grupo = grupo['titulo']
        fotos = grupo['fotos']

        if y_pos - 60 < 140:
            c.showPage()  # Nova página
            desenhar_cabecalho(c, largura_pagina, altura_pagina, caminho_imagem_cabecalho)
            y_pos = altura_pagina - 110

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura_pagina / 2, y_pos, titulo_grupo)
        y_pos -= 30

        x_inicial = 20
        img_largura_max = (largura_pagina - 2 * x_inicial - 2 * 20) / 3
        x_pos = x_inicial
        linha_altura_max = 0

        for i, img_caminho in enumerate(fotos):
            img = redimensionar_imagem(img_caminho, largura_max=img_largura_max * 300 / 72)
            img_largura, img_altura = img.size
            img_largura /= 300 / 72
            img_altura /= 300 / 72

            linha_altura_max = max(linha_altura_max, img_altura)
            if y_pos - img_altura - 60 < 40:
                y_final_bloco = y_pos - linha_altura_max - 20
                c.rect(x_inicial - 10, y_final_bloco - 10, largura_pagina - 40, y_inicial_bloco - y_final_bloco + 30)
                c.showPage()
                desenhar_cabecalho(c, largura_pagina, altura_pagina, caminho_imagem_cabecalho)
                y_pos = altura_pagina - 130
                x_pos = x_inicial
                y_inicial_bloco = y_pos

            c.drawImage(img_caminho, x_pos, y_pos - img_altura, img_largura, img_altura)
            x_pos += img_largura + 20

            if (i + 1) % 3 == 0:
                y_pos -= linha_altura_max + 50
                x_pos = x_inicial
                linha_altura_max = 0

        y_final_bloco = y_pos - linha_altura_max
        c.rect(x_inicial - 10, y_final_bloco - 10, largura_pagina - 40, y_inicial_bloco - y_final_bloco + 30)
        y_pos = y_final_bloco - 60

    c.save()
    return nome_pdf

# Função para gerar o PDF de forma assíncrona
def gerar_pdf_em_thread(titulo_principal, grupos_fotos):
    pdf_gerado = gerar_relatorio_pdf(titulo_principal, grupos_fotos)
    ui.notify(f"PDF '{pdf_gerado}' foi gerado com sucesso!")
    ui.download(pdf_gerado, 'Clique aqui para baixar o PDF gerado')

# Função para iniciar a geração do PDF em uma thread separada
def gerar_pdf_assincrono(titulo_principal_input, grupos_fotos):
    titulo_principal = titulo_principal_input.value
    if not titulo_principal:
        ui.notify("Por favor, insira um título principal.")
        return
    if not grupos_fotos:
        ui.notify("Por favor, adicione ao menos um grupo de fotos.")
        return
    thread = threading.Thread(target=gerar_pdf_em_thread, args=(titulo_principal, grupos_fotos))
    thread.start()
    ui.notify("O PDF está sendo gerado, por favor aguarde...")

# Função para limpar a pasta "uploads"
def limpar_pastas_upload():
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")
    os.makedirs("uploads")

# Interface gráfica usando NiceGUI
def iniciar_interface():
    grupos_fotos = []
    fotos_selecionadas = []
    grupo_atual = 1

    limpar_pastas_upload()

    def handle_file_upload(event):
        pasta_grupo = f"uploads/upload{grupo_atual}"
        os.makedirs(pasta_grupo, exist_ok=True)
        uploaded_file = event.name
        file_path = os.path.join(pasta_grupo, uploaded_file)
        with open(file_path, 'wb') as f:
            f.write(event.content.read())
        fotos_selecionadas.append(file_path)
        ui.notify(f'{len(fotos_selecionadas)} fotos adicionadas ao grupo atual.')

    def adicionar_grupo():
        nonlocal grupo_atual
        titulo_grupo = titulo_input.value
        if not titulo_grupo:
            ui.notify("Por favor, insira um título para o grupo.")
            return
        if not fotos_selecionadas:
            ui.notify("Por favor, selecione fotos para este grupo.")
            return
        grupos_fotos.append({
            'titulo': titulo_grupo,
            'fotos': fotos_selecionadas.copy()
        })
        fotos_selecionadas.clear()
        titulo_input.value = ''
        grupo_atual += 1
        ui.notify(f"Grupo '{titulo_grupo}' adicionado com sucesso!")

    # Função para resetar o projeto
    def resetar_projeto():
        nonlocal grupo_atual
        limpar_pastas_upload()
        grupos_fotos.clear()
        fotos_selecionadas.clear()
        grupo_atual = 1
        ui.notify("Pastas de uploads e grupos resetados com sucesso!")

    ui.label('Gerador de Relatório Fotográfico').classes('text-2xl font-bold')

    with ui.card():
        ui.label('Título principal do relatório:')
        titulo_principal_input = ui.input().classes('w-full')

    with ui.card():
        ui.label('Título do grupo de fotos:')
        titulo_input = ui.input().classes('w-full')
        ui.label('Selecione as fotos para o grupo:')
        ui.upload(on_upload=handle_file_upload, multiple=True)
        ui.button('Adicionar grupo', on_click=adicionar_grupo).classes('bg-blue-500 text-white')

    with ui.card():
        # Agora passamos `titulo_principal_input` corretamente
        ui.button('Gerar PDF', on_click=lambda: gerar_pdf_assincrono(titulo_principal_input, grupos_fotos)).classes('bg-green-500 text-white')

    with ui.card():
        ui.button('Resetar tudo', on_click=resetar_projeto).classes('bg-red-500 text-white')

    ui.run()

iniciar_interface()
