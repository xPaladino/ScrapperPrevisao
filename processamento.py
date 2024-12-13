import pandas as pd
import requests
import re, json, os
from bs4 import BeautifulSoup
from datetime import timedelta
from tkinter import messagebox


import processa_icones
from workbook import formatar_workbook
status_concluido = {"success": False}
arquivo='favoritos.json'

def carregar_favoritos():
    """if os.path.exists(arquivo):
           try:
               with open("favoritos.json", "r") as file:
                   favoritos = json.load(file)
                   if favoritos:
                       # Pega a primeira cidade e seu ID do dicionário
                       cidade, id_cidade = list(favoritos.items())[0]
                       return {"cidade": cidade, "id_cidade": id_cidade}
           except (FileNotFoundError, json.JSONDecodeError):
               pass
           return None
    else:
           return None"""

    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r") as file:
                favoritos = json.load(file)
                if favoritos:
                    return favoritos
        except (json.JSONDecodeError, FileNotFoundError):
            print("Erro ao carregar favoritos. O arquivo pode estar corrompido.")
            return []
    else:
        return []


def salvar_favoritos(novo_favorito):
    arquivo = "favoritos.json"

    # Carrega os favoritos existentes
    favoritos = carregar_favoritos()  # Função carregada anteriormente

    # Verifica se o favorito já existe
    if any(fav["cidade"] == novo_favorito["cidade"] and fav["id_cidade"] == novo_favorito["id_cidade"] for fav in
           favoritos):
        print(f"Favorito já existe: {novo_favorito}")
        return

    # Adiciona o novo favorito
    favoritos.append(novo_favorito)

    try:
        with open(arquivo, "w") as file:
            json.dump(favoritos, file, indent=4)
        print(f"Favorito salvo com sucesso: {novo_favorito}")
    except Exception as e:
        print(f"Erro ao salvar favoritos: {e}")
    """try:
        favoritos = carregar_favoritos()
    except FileNotFoundError:
        favoritos = []

    favoritos.append(favorito)
    with open ("favoritos.json","w") as arquivo:
        json.dump(favoritos, arquivo, indent=4)"""
    """favoritos = carregar_favoritos()
    if not isinstance(favoritos, dict):
        favoritos = {}

    cidade = favorito["cidade"]
    id_cidade = favorito["id_cidade"]
    favoritos[cidade] = id_cidade

    try:
        with open(arquivo, "w") as file:
            json.dump(favoritos, file, indent=4)
        print(f"Cidade {cidade} com ID {id_cidade} salva com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar favoritos: {e}")"""

def buscar_id_cidade(cidade,api_key):
#def buscar_id_cidade(cidade, api_key, arquivo='favoritos.json'):
    #favoritos = carrega_favorito(arquivo)

    #if cidade in favoritos:
    #    print(f'ID {cidade} - {favoritos[cidade]}')
    #    return favoritos[cidade]

    url = f"https://dataservice.accuweather.com/locations/v1/cities/search?q={cidade}&apikey={api_key}"
    try:
        resposta = requests.get(url, verify=False)
        if resposta.status_code == 200:

            print(resposta.json())
            return resposta.json()
        else:
            print(f"Erro ao buscar a cidade {resposta.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Erro identificado {e}")
        return []

def adicionar_anos_nas_datas(data_inicio, numero_dias):

    ano_atual = data_inicio.year
    mes_anterior = data_inicio.month
    dias = []

    for i in range(numero_dias):

        data_alvo = data_inicio + timedelta(days=i)

        if data_alvo.month < mes_anterior:
            ano_atual += 1
        mes_anterior = data_alvo.month

        data_completa = data_alvo.replace(year=ano_atual)
        dias.append(data_completa.strftime('%d/%m/%Y'))
    print(dias)
    return dias


def processar_dados(base_url, headers, numero_dias,cidade,data_inicio):
    lista_datas = adicionar_anos_nas_datas(data_inicio,numero_dias)
    list_pagina_dia = 1
    list_dia, list_temp, list_periodo = [], [], []
    list_condicao, list_sensacao = [], []
    list_icone = []
    list_valor_prob, list_valor_precip, list_valor_horas_prep_dir = [], [], []

    # while True:
    for idx, data_formatada in enumerate(lista_datas):
        url_pagina = f'{base_url}?day={list_pagina_dia}'
        site = requests.get(url_pagina, headers=headers, verify=False)
        soup = BeautifulSoup(site.content, 'html.parser')
        procura_tudo = soup.find_all('div', class_='page-content content-module')

        for item in procura_tudo:
            dia_set = set()
            dia = item.find('span', class_='short-date')
            if dia and dia.text:
                trata_dia = dia.text.strip()
                dia_set.add(trata_dia)
            else:
                messagebox.showwarning(
                    "Atenção",
                    "Ocorreu um erro durante a busca, o limite de data foi excedido.\n"
                    "A busca deve ser num intervalo máximo de 90 dias."
                )
                return


            procura_temperatura = item.find_all('div', class_='weather')
            procura_condicao = item.find_all('div', class_='phrase')
            procura_sensacao = item.find_all('div', class_='real-feel')
            for idx, x in enumerate(procura_temperatura):
                procura_icone = item.find('svg', class_='icon')
                if procura_icone and 'data-src' in procura_icone.attrs:
                    caminho = procura_icone['data-src']
                    codigo = caminho.split('/')[-1].split('.')[0]
                    list_icone.append(codigo)
                else:
                    list_icone.append(None)

                periodo = "Dia" if idx == 0 else "Noite"
                if idx == 0:
                    for cont, y in enumerate(procura_condicao):
                        if cont == 0:
                            trata_cond = y.text.strip()
                            list_condicao.append(trata_cond)
                            print(trata_cond)
                    for cont, y in enumerate(procura_sensacao):
                        if cont == 0:
                            trata_sens = y.text.strip()
                            match_sens = re.search(r"RealFeel®\s*(\d+)",trata_sens)
                            if match_sens:
                                sensacao = match_sens.group(1)
                                print(sensacao)
                                list_sensacao.append(sensacao)
                            #print(match_sens)
                            #list_sensacao.append(match_sens)
                            # print(trata_sens)
                if idx == 1:
                    for cont, z in enumerate(procura_condicao):
                        if cont == 1:
                            trata_cond = z.text.strip()
                            list_condicao.append(trata_cond)
                            print(trata_cond)
                    for cont, z in enumerate(procura_sensacao):
                        if cont == 1:
                            trata_sens = z.text.strip()
                            match_sens = re.search(r"RealFeel®\s*(\d+)", trata_sens)
                            if match_sens:
                                sensacao2 = match_sens.group(1)
                                print(sensacao2)
                                list_sensacao.append(sensacao2)
                            #print(match_sens)

                temperatura = x.find('div', class_='temperature')
                if temperatura:
                    trata_temp = temperatura.text.strip()
                    trata_temp = trata_temp.replace('Mx', '').replace('Mn', '').strip()
                    print(f'{periodo}: Temperatura: {trata_temp}')
                    list_periodo.append(periodo)
                    list_temp.append(trata_temp)
                    list_dia.append(data_formatada) #(", ".join(dia_set))

                procura_precip_dir = item.find_all('div', class_='right')
                procura_precip_esq = item.find_all('div', class_='left')

                if idx < len(procura_precip_dir):
                    itens_precip_dir = procura_precip_dir[idx].find_all('p', class_='panel-item')
                    for precip_dir in itens_precip_dir:
                        nome = precip_dir.contents[0].strip()
                        valor = precip_dir.find('span', class_='value').text.strip()

                        if nome in 'Precipitação':
                            list_valor_precip.append(valor)

                        if nome in 'Horas de precipitação:':
                            try:
                                valor_tratado = float(valor)
                            except ValueError:
                                valor_tratado = 0
                            list_valor_horas_prep_dir.append(valor_tratado)
                        elif nome in 'Probabilidade de trovoadas':
                            list_valor_horas_prep_dir.append(0)

                if idx < len(procura_precip_esq):
                    itens_precip_esq = procura_precip_esq[idx].find_all('p', class_='panel-item')
                    for precip_esq in itens_precip_esq:
                        nome = precip_esq.contents[0].strip()
                        valor = precip_esq.find('span', class_='value').text.strip()

                        if nome in 'Probabilidade de precipitação':
                            list_valor_prob.append(valor)
                        if nome in 'Precipitação':
                            list_valor_precip.append(valor)

        list_pagina_dia += 1

        if list_pagina_dia > numero_dias+1: #captura do GUI
            break

    max_length = max(len(list_dia), len(list_periodo), len(list_temp), len(list_valor_precip),
                     len(list_valor_prob), len(list_valor_horas_prep_dir), len(list_condicao), len(list_sensacao), len(list_icone))

    def pad_list(lst, length):
        return lst + [None] * (length - len(lst))

    list_dia = pad_list(list_dia, max_length)
    list_periodo = pad_list(list_periodo, max_length)
    list_temp = pad_list(list_temp, max_length)
    list_valor_precip = pad_list(list_valor_precip, max_length)
    list_valor_prob = pad_list(list_valor_prob, max_length)
    list_valor_horas_prep_dir = pad_list(list_valor_horas_prep_dir, max_length)
    list_condicao = pad_list(list_condicao,max_length)
    list_sensacao = pad_list(list_sensacao, max_length)
    list_icone = pad_list(list_icone,max_length)
    dados = {
        'Cidade': cidade,
        'Data': list_dia,
        'Periodo': list_periodo,
        'Condição': list_condicao,
        'x': list_temp, #gambi
        'Temperatura': list_temp,
        'Sensação': list_sensacao,
        'Precipitação': list_valor_precip,

        'Probabilidade': list_valor_prob,
        'Horas': list_valor_horas_prep_dir,
        'ID': list_icone

    }
    df = pd.DataFrame(dados)


    return df
