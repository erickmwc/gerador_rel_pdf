from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from nicegui import ui
import os
from starlette.formparsers import MultiPartParser

MultiPartParser.max_file_size = 1024 * 1024 * 5  # 5 MB
# Função para redimensionar a imagem mantendo a proporção e qualidade
def redimensionar_imagem(caminho_imagem, largura_max=900, altura_max=900):
    with Image.open(caminho_imagem) as img:
        # Calcula o redimensionamento proporcional, apenas se necessário
        if img.width > largura_max or img.height > altura_max:
            proporcao = min(largura_max / img.width, altura_max / img.height)
            novo_tamanho = (int(img.width * proporcao), int(img.height * proporcao))
            img = img.resize(novo_tamanho, Image.LANCZOS)  # Redimensiona com alta qualidade
        return img

# Função para gerar o relatório PDF com imagens de alta qualidade e tamanho maior
def gerar_relatorio_pdf(titulo, subtitulo, imagens):
    # Configuração do PDF
    nome_pdf = "relatorio_fotografico.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    largura_pagina, altura_pagina = A4
    dpi = 300  # Define uma resolução de 300 DPI para garantir alta qualidade

    # Adicionar título e subtítulo
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura_pagina / 2, altura_pagina - 50, titulo)
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(largura_pagina / 2, altura_pagina - 80, subtitulo)
    
    y_pos = altura_pagina - 150  # Posição inicial para as imagens
    x_pos_inicial = 20  # Margem inicial da primeira imagem (ajustada para mais espaço)
    margem = 20  # Espaço entre as imagens (ajustado para mais espaço)
    img_largura_max = (largura_pagina - 2 * x_pos_inicial - 2 * margem) / 3  # 3 imagens lado a lado

    x_pos = x_pos_inicial  # Posição horizontal inicial
    linha_altura_max = 0  # A altura máxima de uma linha (para determinar o retângulo)

    for i, img_caminho in enumerate(imagens):
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
            # Desenhar o retângulo ao redor do conjunto de imagens da linha
            c.rect(x_pos_inicial - margem, y_pos - linha_altura_max - margem, 
                   largura_pagina - 2 * x_pos_inicial + 2 * margem, linha_altura_max + 2 * margem)
            
            y_pos -= linha_altura_max + 60  # Desce para a próxima linha (ajustado para mais espaço)
            x_pos = x_pos_inicial  # Resetar posição horizontal para a nova linha
            linha_altura_max = 0  # Resetar a altura máxima para a nova linha

            # Verificar se há espaço suficiente na página para uma nova linha
            if y_pos < 150:  # Se não houver espaço, adicionar uma nova página
                c.showPage()
                y_pos = altura_pagina - 50
                x_pos = x_pos_inicial  # Resetar x_pos para a nova página

        # Inserir a imagem no PDF
        temp_img_path = f"temp_img_{i}.png"
        img.save(temp_img_path)
        c.drawImage(temp_img_path, x_pos, y_pos - img_altura, img_largura, img_altura)

        # Atualizar a posição horizontal para a próxima imagem (na mesma linha)
        x_pos += img_largura + margem

    # Desenhar o retângulo ao redor da última linha de imagens (se houver imagens restantes)
    if len(imagens) % 3 != 0:
        c.rect(x_pos_inicial - margem, y_pos - linha_altura_max - margem, 
               largura_pagina - 2 * x_pos_inicial + 2 * margem, linha_altura_max + 2 * margem)

    # Finalizar e salvar o PDF
    c.save()
    print(f"Relatório PDF '{nome_pdf}' gerado com sucesso!")

    return nome_pdf


# Interface gráfica usando NiceGUI
def iniciar_interface():
    imagens_selecionadas = []

    def handle_file_upload(event):
    # Criar diretório para armazenar uploads temporários
        if not os.path.exists("uploads"):
            os.makedirs("uploads")

        # Acessar o arquivo do evento de upload
        uploaded_file = event.name  # Nome do arquivo
        file_path = os.path.join("uploads", uploaded_file)

        # Salvar o conteúdo do arquivo corretamente
        with open(file_path, 'wb') as f:
            f.write(event.content.read())  # Ler o conteúdo binário corretamente
        imagens_selecionadas.append(file_path)

        # Notificar o usuário da quantidade de imagens carregadas
        ui.notify(f'{len(imagens_selecionadas)} imagens selecionadas.')


    def gerar_pdf():
        # Pegar os valores do título e subtítulo
        titulo = titulo_input.value
        subtitulo = subtitulo_input.value

        if not imagens_selecionadas:
            ui.notify("Por favor, selecione as imagens antes de gerar o PDF.")
            return

        # Gerar o relatório PDF
        pdf_gerado = gerar_relatorio_pdf(titulo, subtitulo, imagens_selecionadas)

        # Exibir link para download do PDF
        with ui.card():
            ui.link(f'Clique aqui para baixar o PDF gerado', pdf_gerado)
            ui.notify(f"Relatório PDF '{pdf_gerado}' gerado com sucesso!")

    # Título da página
    ui.label('Gerador de Relatório Fotográfico').classes('text-2xl font-bold')

    # Inputs para título e subtítulo
    with ui.card():
        ui.label('Título do relatório:')
        titulo_input = ui.input().classes('w-full')

        ui.label('Subtítulo do relatório:')
        subtitulo_input = ui.input().classes('w-full')

    # Upload de arquivos
    with ui.card():
        ui.label('Selecione as imagens para o relatório:')
      #  ui.upload(on_upload=handle_file_upload, multiple=True)
        ui.upload(on_upload=handle_file_upload, multiple=True)


    # Botão para gerar o PDF
    with ui.card():
        ui.button('Gerar PDF', on_click=gerar_pdf).classes('bg-blue-500 text-white')

    # Executar o servidor
    ui.run()


iniciar_interface()
