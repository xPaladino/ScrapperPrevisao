import requests
import os
import cairosvg
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from PIL import Image as PILImage

# Cria as pastas para salvar os ícones SVG e PNG, caso não existam
os.makedirs('weather_icons', exist_ok=True)
os.makedirs('weather_icons_png', exist_ok=True)

# Define o cabeçalho para imitar um navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
}

# Baixa e converte os ícones para PNG
for i in range(1, 45):
    svg_url = f"https://www.accuweather.com/images/weathericons/{i}.svg"
    response = requests.get(svg_url, headers=headers)

    if response.status_code == 200:
        svg_path = f"weather_icons/{i}.svg"
        png_path = f"weather_icons_png/{i}.png"

        # Salva o SVG
        with open(svg_path, 'wb') as file:
            file.write(response.content)

        # Converte SVG para PNG
        cairosvg.svg2png(url=svg_path, write_to=png_path)

        # Redimensiona a imagem para um tamanho adequado (exemplo: 50x50 pixels)
        with PILImage.open(png_path) as img:
            img_resized = img.resize((25, 25))  # Redimensiona para 50x50 pixels
            img_resized.save(png_path)  # Sobrescreve a imagem PNG com o tamanho ajustado
        print(f"Ícone {i} baixado e redimensionado.")
    else:
        print(f"Ícone {i} não encontrado ou acesso bloqueado.")

# Criar planilha Excel e inserir as imagens
wb = Workbook()
ws = wb.active
ws.title = "Weather Icons"

# Adiciona as imagens PNG na planilha com espaçamento
for i in range(1, 45):
    png_path = f"weather_icons_png/{i}.png"

    if os.path.exists(png_path):
        img = Image(png_path)
        cell_row = (i * 2) - 1  # Coloca as imagens em linhas ímpares para espaçamento
        ws.add_image(img, f"A{cell_row}")  # Insere a imagem na coluna A
        print(f"Ícone {i} adicionado ao Excel na linha {cell_row}.")
    else:
        print(f"PNG {i} não encontrado para adicionar ao Excel.")

# Salva a planilha
wb.save("WeatherIcons.xlsx")
print("Processo completo: Ícones redimensionados e espaçados adicionados ao Excel!")
