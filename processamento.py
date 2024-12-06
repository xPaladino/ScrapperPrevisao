import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import timedelta
from tkinter import messagebox


import processa_icones
from workbook import formatar_workbook
status_concluido = {"success": False}

def buscar_id_cidade(cidade,api_key):
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
    list_condicao = []
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
                if idx == 1:
                    for cont, z in enumerate(procura_condicao):
                        if cont == 1:
                            trata_cond = z.text.strip()
                            list_condicao.append(trata_cond)

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
                     len(list_valor_prob), len(list_valor_horas_prep_dir), len(list_condicao), len(list_icone))

    def pad_list(lst, length):
        return lst + [None] * (length - len(lst))

    list_dia = pad_list(list_dia, max_length)
    list_periodo = pad_list(list_periodo, max_length)
    list_temp = pad_list(list_temp, max_length)
    list_valor_precip = pad_list(list_valor_precip, max_length)
    list_valor_prob = pad_list(list_valor_prob, max_length)
    list_valor_horas_prep_dir = pad_list(list_valor_horas_prep_dir, max_length)
    list_condicao = pad_list(list_condicao,max_length)
    list_icone = pad_list(list_icone,max_length)
    dados = {
        'Cidade': cidade,
        'Data': list_dia,
        'Periodo': list_periodo,
        'Condição': list_condicao,
        'x': list_temp, #gambi
        'Temperatura': list_temp,
        'Precipitação': list_valor_precip,

        'Probabilidade': list_valor_prob,
        'Horas': list_valor_horas_prep_dir,
        'ID': list_icone

    }
    df = pd.DataFrame(dados)


    return df
