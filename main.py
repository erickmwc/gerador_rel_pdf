import os
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from nicegui import ui



# Função para redimensionar a imagem mantendo a proporção e alta qualidade
def redimensionar_imagem(caminho_imagem, largura_max=900, altura_max=900):
    with Image.open(caminho_imagem) as img:
        if img.width > largura_max or img.height > altura_max:
            proporcao = min(largura_max / img.width, altura_max / img.height)
            novo_tamanho = (int(img.width * proporcao), int(img.height * proporcao))
            img = img.resize(novo_tamanho, Image.LANCZOS)  # Redimensiona com alta qualidade
        return img

# Função para gerar o relatório PDF com grupos de fotos e títulos
def gerar_relatorio_pdf(titulo_principal, grupos_fotos):
    nome_pdf = f"uploads/relatorio_fotografico.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    largura_pagina, altura_pagina = A4
    dpi = 300  # Define uma resolução de 300 DPI para garantir alta qualidade

    # Adicionar título principal
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura_pagina / 2, altura_pagina - 50, titulo_principal)
    
    y_pos = altura_pagina - 100  # Posição inicial, ajustada para começar após o título principal
    
    for grupo in grupos_fotos:
        titulo_grupo = grupo['titulo']
        fotos = grupo['fotos']

        # Verificar se há espaço para pelo menos uma linha de imagens junto com o título
        if y_pos - 60 < 160:  # Se não houver espaço suficiente para o título + imagens
            c.showPage()  # Adicionar uma nova página
            y_pos = altura_pagina - 50  # Resetar y_pos para a nova página

        # Adicionar o título do grupo
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura_pagina / 2, y_pos, titulo_grupo)
        y_pos -= 30  # Mover a posição abaixo do título do grupo

        # Definir limites iniciais para o retângulo do bloco
        y_inicial_bloco = y_pos  # Ponto superior do bloco
        x_inicial = 20  # Margem esquerda do bloco
        x_final = largura_pagina - 20  # Margem direita do bloco

        # Definir largura máxima das imagens (3 imagens lado a lado)
        img_largura_max = (largura_pagina - 2 * x_inicial - 2 * 20) / 3  # Três imagens lado a lado com margens

        x_pos = x_inicial  # Posição horizontal inicial
        linha_altura_max = 0  # A altura máxima de uma linha

        for i, img_caminho in enumerate(fotos):
            img = redimensionar_imagem(img_caminho, largura_max=img_largura_max * dpi / 72)
            img_largura, img_altura = img.size

            # Ajustar o tamanho da imagem para o DPI correto
            img_largura /= dpi / 72
            img_altura /= dpi / 72

            linha_altura_max = max(linha_altura_max, img_altura)

            # Verificar se há espaço suficiente para a imagem
            if y_pos - img_altura - 60 < 40:  # Conferir se a imagem cabe na página atual
                # Desenhar o retângulo do bloco antes de mudar de página
                y_final_bloco = y_pos - linha_altura_max - 20  # Ponto inferior do bloco
                c.rect(x_inicial - 10, y_final_bloco - 10, x_final - x_inicial + 20, y_inicial_bloco - y_final_bloco + 30)

                c.showPage()  # Adicionar uma nova página
                y_pos = altura_pagina - 50  # Resetar y_pos para a nova página
                x_pos = x_inicial  # Resetar posição horizontal

                # Redefinir y_inicial_bloco para a nova página
                y_inicial_bloco = y_pos

            # Desenhar a imagem no PDF
            c.drawImage(img_caminho, x_pos, y_pos - img_altura, img_largura, img_altura)
            x_pos += img_largura + 20  # Atualizar posição horizontal

            # Quando 3 imagens forem adicionadas, resetar a linha
            if (i + 1) % 3 == 0:
                y_pos -= linha_altura_max + 60  # Mover para a próxima linha
                x_pos = x_inicial  # Resetar a posição horizontal
                linha_altura_max = 0  # Resetar altura máxima para a nova linha

        # Após desenhar todas as imagens do grupo, definir a posição inferior do retângulo
        y_final_bloco = y_pos - linha_altura_max - 20  # Ponto inferior do bloco

        # Desenhar o retângulo ao redor do bloco de imagens (contendo todas as imagens do grupo)
        c.rect(x_inicial - 10, y_final_bloco - 10, x_final - x_inicial + 20, y_inicial_bloco - y_final_bloco + 30)

        # Atualizar a posição para o próximo grupo
        y_pos = y_final_bloco - 60





    # Finalizar e salvar o PDF
    c.save()
    return nome_pdf

# Função para limpar a pasta "uploads"
def limpar_pastas_upload():
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")  # Remover a pasta inteira
    os.makedirs("uploads")  # Recriar a pasta vazia

# Interface gráfica usando NiceGUI
def iniciar_interface():
    grupos_fotos = []  # Lista para armazenar os grupos de fotos
    fotos_selecionadas = []  # Lista temporária para armazenar as fotos do grupo atual
    grupo_atual = 1  # Contador de grupos para nomear as pastas

    # Limpar todas as pastas de uploads ao iniciar
    limpar_pastas_upload()

    def handle_file_upload(event):
        # Criar diretório específico para o grupo atual
        pasta_grupo = f"uploads/upload{grupo_atual}"
        os.makedirs(pasta_grupo, exist_ok=True)

        # Salvar as fotos carregadas na pasta do grupo atual
        uploaded_file = event.name
        file_path = os.path.join(pasta_grupo, uploaded_file)

        with open(file_path, 'wb') as f:
            f.write(event.content.read())

        fotos_selecionadas.append(file_path)
        ui.notify(f'{len(fotos_selecionadas)} fotos adicionadas ao grupo atual.')

    def adicionar_grupo():
        nonlocal grupo_atual  # Permitir que a função modifique o contador de grupos
        titulo_grupo = titulo_input.value

        if not titulo_grupo:
            ui.notify("Por favor, insira um título para o grupo.")
            return

        if not fotos_selecionadas:
            ui.notify("Por favor, selecione fotos para este grupo.")
            return

        # Adicionar o grupo de fotos e criar a nova pasta para o próximo grupo
        grupos_fotos.append({
            'titulo': titulo_grupo,
            'fotos': fotos_selecionadas.copy()  # Clonar a lista de fotos
        })

        # Limpar a lista de fotos para o próximo grupo e atualizar o contador de grupos
        fotos_selecionadas.clear()
        titulo_input.value = ''
        grupo_atual += 1

        ui.notify(f"Grupo '{titulo_grupo}' adicionado com sucesso!")

    def gerar_pdf():
        titulo_principal = titulo_principal_input.value

        if not titulo_principal:
            ui.notify("Por favor, insira um título principal para o relatório.")
            return

        if not grupos_fotos:
            ui.notify("Por favor, adicione ao menos um grupo de fotos.")
            return


        # Gerar o relatório PDF
        pdf_gerado = gerar_relatorio_pdf(titulo_principal, grupos_fotos)

        with ui.card():
            # ui.link(f'Clique aqui para baixar o PDF gerado', pdf_gerado)
           # ui.link(f'Clique aqui para baixar o PDF gerado', '/download_pdf')
            ui.download(pdf_gerado, 'Clique aqui para baixar o PDF gerado')
            ui.notify(f"Relatório PDF '{pdf_gerado}' gerado com sucesso!")

    # Função para resetar as pastas de uploads e grupos
    def resetar_projeto():
        nonlocal grupo_atual
        limpar_pastas_upload()
        grupos_fotos.clear()  # Limpar os grupos de fotos
        fotos_selecionadas.clear()  # Limpar as fotos selecionadas
        grupo_atual = 1  # Resetar o contador de grupos
        ui.notify("Pastas de uploads e grupos resetados com sucesso!")

    # Interface gráfica usando NiceGUI
    ui.label('Gerador de Relatório Fotográfico').classes('text-2xl font-bold')

    # Input para o título principal
    with ui.card():
        ui.label('Título principal do relatório:')
        titulo_principal_input = ui.input().classes('w-full')

    # Inputs para o título do grupo e upload de fotos
    with ui.card():
        ui.label('Título do grupo de fotos:')
        titulo_input = ui.input().classes('w-full')

        ui.label('Selecione as fotos para o grupo:')
        ui.upload(on_upload=handle_file_upload, multiple=True)

        ui.button('Adicionar grupo', on_click=adicionar_grupo).classes('bg-blue-500 text-white')

    # Botão para gerar o PDF
    with ui.card():
        ui.button('Gerar PDF', on_click=gerar_pdf).classes('bg-green-500 text-white')
    

    # Botão para resetar as pastas de uploads e grupos
    with ui.card():
        ui.button('Resetar tudo', on_click=resetar_projeto).classes('bg-red-500 text-white')

    # Executar o servidor
    ui.run()


iniciar_interface()
