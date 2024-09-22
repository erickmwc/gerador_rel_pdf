import os
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from nicegui import ui

# Função para redimensionar a imagem mantendo a proporção e alta qualidade
def redimensionar_imagem(caminho_imagem, largura_max=600, altura_max=600):
    with Image.open(caminho_imagem) as img:
        # Calcula o redimensionamento proporcional, apenas se necessário
        if img.width > largura_max or img.height > altura_max:
            proporcao = min(largura_max / img.width, altura_max / img.height)
            novo_tamanho = (int(img.width * proporcao), int(img.height * proporcao))
            img = img.resize(novo_tamanho, Image.LANCZOS)  # Redimensiona com alta qualidade
        return img

# Função para gerar o relatório PDF com grupos de fotos e títulos
def gerar_relatorio_pdf(titulo_principal, grupos_fotos):
    nome_pdf = "relatorio_fotografico.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    largura_pagina, altura_pagina = A4
    dpi = 300  # Define uma resolução de 300 DPI para garantir alta qualidade

    # Adicionar título principal
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura_pagina / 2, altura_pagina - 50, titulo_principal)
    
    y_pos = altura_pagina - 100  # Posição inicial, ajustada para começar após o título principal
    
    for grupo in grupos_fotos:
        # Adicionar o título do grupo de fotos
        titulo_grupo = grupo['titulo']
        fotos = grupo['fotos']
        
        # Adicionar o título do grupo
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(largura_pagina / 2, y_pos, titulo_grupo)
        y_pos -= 40  # Mover a posição abaixo do título do grupo
        
        x_pos_inicial = 20  # Margem inicial da primeira imagem
        margem = 20  # Espaço entre as imagens
        img_largura_max = (largura_pagina - 2 * x_pos_inicial - 2 * margem) / 3  # 3 imagens lado a lado

        x_pos = x_pos_inicial  # Posição horizontal inicial
        linha_altura_max = 0  # A altura máxima de uma linha (para determinar o retângulo)
        
        for i, img_caminho in enumerate(fotos):
            # Redimensionar a imagem apenas se necessário, mantendo a proporção
            img = redimensionar_imagem(img_caminho, largura_max=img_largura_max * dpi / 72)
            img_largura, img_altura = img.size

            # Ajustar o tamanho da imagem para a escala correta no PDF (72 DPI padrão)
            img_largura /= dpi / 72
            img_altura /= dpi / 72

            # Atualiza a altura máxima da linha, para ajustar o retângulo ao redor das 3 imagens
            linha_altura_max = max(linha_altura_max, img_altura)

            # Se a imagem não couber na linha atual, mover para a próxima linha
            if i % 3 == 0 and i != 0:
                c.rect(x_pos_inicial - margem, y_pos - linha_altura_max - margem, 
                       largura_pagina - 2 * x_pos_inicial + 2 * margem, linha_altura_max + 2 * margem)
                
                y_pos -= linha_altura_max + 60  # Desce para a próxima linha
                x_pos = x_pos_inicial  # Resetar posição horizontal para a nova linha
                linha_altura_max = 0  # Resetar a altura máxima para a nova linha

                if y_pos < 150:  # Se não houver espaço, adicionar uma nova página
                    c.showPage()
                    y_pos = altura_pagina - 50
                    x_pos = x_pos_inicial  # Resetar x_pos para a nova página

            # Inserir a imagem no PDF
            c.drawImage(img_caminho, x_pos, y_pos - img_altura, img_largura, img_altura)

            # Atualizar a posição horizontal para a próxima imagem (na mesma linha)
            x_pos += img_largura + margem

        if len(fotos) % 3 != 0:
            c.rect(x_pos_inicial - margem, y_pos - linha_altura_max - margem, 
                   largura_pagina - 2 * x_pos_inicial + 2 * margem, linha_altura_max + 2 * margem)

        y_pos -= linha_altura_max + 80

    # Finalizar e salvar o PDF
    c.save()
    return nome_pdf

# Função para limpar a pasta "uploads" ao iniciar
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
            ui.link(f'Clique aqui para baixar o PDF gerado', pdf_gerado)
            ui.notify(f"Relatório PDF '{pdf_gerado}' gerado com sucesso!")

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

    # Executar o servidor
    ui.run()


iniciar_interface()
