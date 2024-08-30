import pandas as pd
import requests
from bs4 import BeautifulSoup
from workbook import formatar_workbook

def processar_dados(base_url, headers, numero_dias,cidade):
    list_pagina_dia = 1
    list_dia, list_temp, list_periodo = [], [], []
    list_condicao = []
    list_valor_prob, list_valor_precip, list_valor_horas_prep_dir = [], [], []

    while True:
        url_pagina = f'{base_url}?day={list_pagina_dia}'
        site = requests.get(url_pagina, headers=headers)
        soup = BeautifulSoup(site.content, 'html.parser')
        procura_tudo = soup.find_all('div', class_='page-content content-module')

        for item in procura_tudo:
            dia_set = set()
            dia = item.find('span', class_='short-date')
            trata_dia = dia.text.strip()
            dia_set.add(trata_dia)

            procura_temperatura = item.find_all('div', class_='weather')
            procura_condicao = item.find_all('div', class_='phrase')


            for idx, x in enumerate(procura_temperatura):
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
                    list_dia.append(", ".join(dia_set))

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
                     len(list_valor_prob), len(list_valor_horas_prep_dir), len(list_condicao))

    def pad_list(lst, length):
        return lst + [None] * (length - len(lst))

    list_dia = pad_list(list_dia, max_length)
    list_periodo = pad_list(list_periodo, max_length)
    list_temp = pad_list(list_temp, max_length)
    list_valor_precip = pad_list(list_valor_precip, max_length)
    list_valor_prob = pad_list(list_valor_prob, max_length)
    list_valor_horas_prep_dir = pad_list(list_valor_horas_prep_dir, max_length)
    list_condicao = pad_list(list_condicao,max_length)

    dados = {
        'Cidade': cidade,
        'Data': list_dia,
        'Periodo': list_periodo,
        'Condição': list_condicao,
        'Temperatura': list_temp,
        'Precipitação': list_valor_precip,
        'Probabilidade': list_valor_prob,
        'Horas': list_valor_horas_prep_dir
    }
    df = pd.DataFrame(dados)

    return df
