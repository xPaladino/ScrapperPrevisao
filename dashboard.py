import pandas as pd
import plotly.express as px
import plotly.io as pio
from cairosvg.colors import color
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from unicodedata import category


def ler_excel(file_path):
    return pd.read_excel(file_path)


def gerar_grafico(df, grafico_path):
    # ajustes das colunas
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.sort_values(by=['Data','Precipitação'], ascending=[True,True])
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')

    df['Precipitação'] = df["Precipitação"].str.replace(' mm','').astype(float)
    #df = df.sort_values(by='Precipitação',ascending=True)
    # grafico
    df['Periodo'] = df['Data'].apply(lambda x: 'Dia' if int(x.split('/')[0]) % 2 == 0 else 'Noite')
    fig = px.bar(df, x='Data', y='Precipitação',  title="Precipitação")
    #fig.update_yaxes(tickformat="1.f")
    fig.update_traces(
       # marker=dict(color='#33ff74'),
        text=df.apply(lambda row: f'{row["Precipitação"]:.2f} mm ({row["Periodo"]})', axis=1),
        textposition='inside',
        texttemplate='%{text}',
       # insidetextanchor='middle',
        textangle = 0,
        marker=dict(color=df['Periodo'].map({'Dia': '#33ff74', 'Noite': '#ff5733'})),
        textfont=dict(size=30,color='black',family='Arial')
    )
    fig.update_layout(
        plot_bgcolor='black',  # Cor de fundo do gráfico
        paper_bgcolor='black',  # Cor de fundo do painel (toda a área do gráfico)
        font_color='white',  # Cor da fonte (texto)
        title_font_color='white',  # Cor do título
        xaxis=dict(
            title_font_color='white',  # Cor do título do eixo X
            tickfont_color='white'
            # Cor dos ticks do eixo X
        ),
        yaxis=dict(
            title_font_color='white',  # Cor do título do eixo Y
            tickfont_color='white',
            tickformat="2.f"
        )
    )
    fig.write_image(grafico_path)
    #fig.show()
def inserir_imagem_no_excel(file_path, imagem_path):

    wb = load_workbook(file_path)
    ws = wb.active
    img = Image(imagem_path)
    ws.add_image(img, 'K2')

    wb.save(file_path)


def gerar_dashboard(file_path, diretorio_saida):

    df = ler_excel(file_path)
    grafico_path = "grafico_temperaturas.png"
    gerar_grafico(df, grafico_path)
    inserir_imagem_no_excel(file_path, grafico_path)

    print(f"Dashboard gerado e salvo em {file_path}")