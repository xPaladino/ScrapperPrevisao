import tkinter as tk

from tkinter import ttk, messagebox, filedialog, Toplevel
from processamento import carregar_favoritos, salvar_favoritos
import processamento
import processa_icones
from PIL import Image, ImageTk
from datetime import datetime
from unidecode import unidecode
import threading
import os
import json
from workbook import formatar_workbook
import time

status_concluido = {"success": False}
api_key = ""

def carregar_api_key():
    global api_key
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
            api_key = config.get("api_key", "")
    except FileNotFoundError:
        # Caso o arquivo não exista, não faz nada
        pass


def redimensionar_gif(image, tamanho):
    frames = []
    try:
        while True:
            frame = image.copy()
            frame = frame.resize(tamanho, Image.LANCZOS)  # Redimensiona o frame
            frames.append(ImageTk.PhotoImage(frame))
            image.seek(image.tell() + 1)
    except EOFError:
        pass
    return frames

def atualiza_gif(label, frames, index):
    if label.winfo_exists():
        label.configure(image=frames[index])
        index = (index + 1) % len(frames)
        label.after(100, atualiza_gif, label, frames, index)

def tela_carregamento():
    carregamento = tk.Toplevel()
    carregamento.iconbitmap('stitch_ico.ico')
    carregamento.title("Aguarde")
    carregamento.geometry("300x300")

    gif = Image.open("stitch.gif")
    tamanho = (100,120)
    frames = redimensionar_gif(gif,tamanho)

    gif_label = tk.Label(carregamento)
    gif_label.pack(padx=30,pady=30)
    tk.Label(carregamento, text="Processando, por favor aguarde...", padx=20, pady=20).pack()
    if frames:
        atualiza_gif(gif_label, frames, 0)

    timer_label = tk.Label(carregamento, text="Tempo decorrido: 0s")
    timer_label.pack(pady=10)

    start_time = time.time()

    def atualizar_timer():
        if status_concluido["success"]:

            return

        elapsed_time = int(time.time() - start_time)
        timer_label.config(text=f"Tempo decorrido: {elapsed_time}s")
        carregamento.after(1000, atualizar_timer)  # Atualiza a cada 1 segundo

    atualizar_timer()
    carregamento.grab_set()
    return carregamento


# logica para escolha de cidade

def selecionar_cidade(dados):
    """
    Exibe uma interface gráfica para o usuário selecionar uma cidade.
    """
    # Usar uma variável para armazenar o valor da cidade selecionada
    resultado_selecao = None

    def on_button_click(index):
        """
        Quando o botão for clicado, define a cidade selecionada e fecha a janela.
        """
        nonlocal resultado_selecao
        selecionada = dados[index]
        resultado_selecao = selecionada["Key"]  # A chave da cidade selecionada
        print(f"Chave selecionada: {resultado_selecao}")

        root.quit()  # Fecha a janela após a seleção
        root.destroy()

    root = tk.Tk()
    root.title("Seleção de Cidade")
    root.iconbitmap('stitch_ico.ico')
    label = tk.Label(root, text=f"Olá, encontrei {len(dados)} resultados para a cidade informada:")
    label.pack(pady=10)

    for i, item in enumerate(dados):
        cidade = item["LocalizedName"]
        estado = item["AdministrativeArea"]["LocalizedName"]
        pais = item["Country"]["LocalizedName"]
        texto_botao = f"{cidade}, {estado}, {pais}"
        button = tk.Button(root, text=texto_botao, command=lambda idx=i: on_button_click(idx))
        button.pack(pady=5)

    root.mainloop()  # Agora mantemos o loop até que o usuário selecione uma cidade

    # Agora resultado_selecao deve conter a chave da cidade selecionada
    if resultado_selecao is None:
        print("Nenhuma cidade foi selecionada.")
    return resultado_selecao

def iniciar_processamento(id_cidade, cidade, dias, caminho_arquivo, data_inicio):
    """
    Função que realiza o processamento com a cidade selecionada.
    """
    def processar():
        nonlocal id_cidade, cidade, dias, caminho_arquivo, data_inicio

        # Formata a URL usando o ID da cidade selecionada
        base_url = (f'https://www.accuweather.com/pt/{cidade}/'
                    f'{id_cidade}/daily-weather-forecast/{id_cidade}')

        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/86.0.4240.198 Safari/537.36"
        }

        # Processa os dados
        df = processamento.processar_dados(base_url, headers, dias, cidade, data_inicio)
        print(cidade)
        # Define o caminho do arquivo
        if not caminho_arquivo.endswith('.xlsx'):
            caminho_arquivo += '.xlsx'

        diretorio = os.path.dirname(caminho_arquivo)
        if not os.path.exists(diretorio):
            try:
                os.makedirs(diretorio)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível criar o diretório: {e}")
                status_concluido["success"] = False
                return

        try:
            # Salva o arquivo no Excel
            df.to_excel(caminho_arquivo, index=False)

            try:
                # Adiciona ícones ao Excel
                processa_icones.adicionar_icones_ao_excel(df, caminho_arquivo)

            except Exception as e:
                print(f"Erro processando ícones: {e}")
                messagebox.showerror("Erro", f"Erro ao adicionar ícones: {e}")
            messagebox.showinfo(
                "Sucesso",
                f"Resultados referentes à cidade: {cidade} (ID: {id_cidade})\nDados salvos em {caminho_arquivo}"
            )
            status_concluido["success"] = True
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo: {e}")
            status_concluido["success"] = False

    carregamento = tela_carregamento()
    # Inicia o processamento em uma nova thread para não bloquear a interface
    threading.Thread(target=processar, daemon=True).start()

    def verificar_status():
        if status_concluido["success"]:
            carregamento.destroy()
            status_concluido["success"] = False
        else:
            carregamento.after(1000, verificar_status)

    # Inicia a verificação do status
    verificar_status()



def executar_processamento(cidade, dias, caminho_arquivo, data_inicio):
    try:
        print(cidade)
        favoritos = carregar_favoritos()
        #print(favoritos['cidade'])
        if favoritos:  # Verifica se existem favoritos carregados
            # Procura pela cidade nos favoritos
            favorito_encontrado = next((fav for fav in favoritos if fav['cidade'] == cidade), None)

            if favorito_encontrado:
                usar_favorito = messagebox.askyesno(
                    "Cidade Encontrada",
                    f"Cidade de {favorito_encontrado['cidade']} identificada na nossa base de dados.\n"
                    f"Deseja consulta-lá?\nID: {favorito_encontrado['id_cidade']}"
                )
                if usar_favorito:
                    # Chama a função de iniciar o processamento diretamente com o favorito
                    id_cidade = favorito_encontrado['id_cidade']
                    iniciar_processamento(id_cidade, cidade, dias, caminho_arquivo, data_inicio)
                    return
        else:
            print("Nenhum favorito encontrado ou arquivo inexistente.")

        # Se não encontrou ou não usou o favorito, segue o processamento normal
        selecionar_e_processar(cidade, dias, caminho_arquivo, data_inicio)

    except Exception as e:
        print(f"Erro ao executar o processamento: {e}")


def selecionar_e_processar(cidade, dias, caminho_arquivo, data_inicio):
    # Realiza a busca pela cidade usando buscar_id_cidade
    dados_cidades = processamento.buscar_id_cidade(cidade, api_key)
    print(dados_cidades)
    if not dados_cidades:
        messagebox.showerror("Erro", "Nenhuma cidade foi encontrada.")
        return

    # Abre a interface gráfica para o usuário selecionar uma cidade
    try:
        id_cidade = selecionar_cidade(dados_cidades)

        #favorito = {"id_cidade": id_cidade, "cidade": cidade}
        favorito = {"cidade": cidade, "id_cidade": id_cidade}
        print(cidade)
        salvar_favorito = messagebox.askyesno(
            "Salvar?",
            f"Deseja salvar essa cidade como favorita?\nCidade: {cidade} (ID: {id_cidade})"
        )
        if salvar_favorito:
            salvar_favoritos(favorito)
        print(id_cidade)
        # Chama a função de iniciar o processamento com a cidade selecionada
        iniciar_processamento(id_cidade, cidade, dias, caminho_arquivo, data_inicio)

    except Exception as e:
        print(f"não consegui {e}")

def formatar_cidade(cidade):
    cidade_formatada = unidecode(cidade).replace(' ', '').lower()
    print(cidade_formatada)
    return cidade_formatada


def browser(entry):
    seleciona = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Arquivos Excel", "*.xlsx")],
        title="Salvar como",
        confirmoverwrite=True
    )
    if seleciona:
        entry.delete(0, tk.END)
        entry.insert(tk.END, seleciona)
    else:
        messagebox.showwarning("Atenção", "Por favor, selecione um local válido para salvar o arquivo.")

def criar_menu(root):

    menu_principal = tk.Menu(root)

    menu_arquivo = tk.Menu(menu_principal, tearoff=0)

    menu_arquivo.add_separator()
    menu_arquivo.add_command(label="Sair", command=root.quit)

    menu_config = tk.Menu(menu_principal, tearoff=0)
    menu_config.add_command(label="Abrir Configurações", command=abrir_config)

    menu_principal.add_cascade(label="Arquivo", menu=menu_arquivo)
    menu_principal.add_cascade(label="Configurações", menu=menu_config)

    root.config(menu=menu_principal)


def abrir_config():
    global api_key
    def salvar_config():
        global api_key
        api_key = entry_api_key.get()  # Salva a chave da API na variável global
        salvar_api_key()  # Salva a chave da API no arquivo
        label_api_key.config(text=f"Chave da API: {api_key}")  # Atualiza a label para exibir a chave salva
        messagebox.showinfo("Configurações", "Chave da API salva com sucesso!")
        config_window.destroy()

    config_window = Toplevel()
    config_window.title("Configurações")
    config_window.geometry("300x150")
    config_window.iconbitmap('stitch_ico.ico')

    label_api_key = tk.Label(config_window, text="Chave da API:")
    label_api_key.pack(pady=10)

    entry_api_key = tk.Entry(config_window, width=30)
    entry_api_key.pack(pady=10)

    # Tentar carregar a chave da API previamente salva
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
            saved_api_key = config.get("api_key", "")
            if saved_api_key:
                entry_api_key.insert(0, saved_api_key)
                label_api_key.config(text=f"Chave da API: {saved_api_key}")
    except FileNotFoundError:
        saved_api_key = None

    button_salvar = tk.Button(config_window, text="Salvar", command=salvar_config)
    button_salvar.pack(pady=10)

    config_window.grab_set()

def salvar_api_key():

    with open("config.json", "w") as file:
        json.dump({"api_key": api_key}, file)

def criar_tela_principal_com_abas(root):
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    aba_principal = tk.Frame(notebook)
    notebook.add(aba_principal, text="Principal")
    criar_interface_principal(aba_principal)


def criar_interface_principal(parent):
    local_label = tk.Label(parent, text="Cidade:")
    local_label.grid(row=1, column=0, padx=15, pady=5, sticky="w")

    data_inicio = tk.Label(parent, text="Data Inicial:")
    data_inicio.grid(row=2, column=0, padx=15, pady=5, sticky="w")

    data_fim = tk.Label(parent, text="Data Final:")
    data_fim.grid(row=3, column=0, padx=15, pady=5, sticky="w")

    salvar_label = tk.Label(parent, text="Diretório")
    salvar_label.grid(row=4, column=0, padx=15, pady=5, sticky="w")

    def handle_keypress_nohour(event, entry_widget):
        # responsavel por alterar o campo para dia/mes/ano
        if event.char.isdigit() or event.keysym == 'BackSpace' or event.keysym == 'Tab':  # or event.char in ["/", ":", " "]:
            resultado = entry_widget.get()
            if len(resultado) == 2 and event.char.isdigit():
                entry_widget.insert(tk.END, '/')
            elif len(resultado) == 5 and event.char.isdigit():
                entry_widget.insert(tk.END, '/')
            elif len(resultado) >= 9 and event.char.isdigit():
                entry_widget.delete(9, tk.END)
            return True
        return "break"

    def handle_nokeypress(event):
        if event.keysym in ['BackSpace', 'Tab']:
            return True
        return "break"

    def handle_keypress_nochar(event, entry_widget):
        if event.char.isalpha() or event.keysym in ['BackSpace', 'Tab', 'space']:
            return True
        return "break"

    local = tk.Entry(parent, width=12)
    local.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    local.bind("<Key>", lambda event: handle_keypress_nochar(event, local))

    inicio_dado = tk.Entry(parent, width=12)
    inicio_dado.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    inicio_dado.bind("<Key>", lambda event: handle_keypress_nohour(event, inicio_dado))

    fim_dado = tk.Entry(parent, width=12)
    fim_dado.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    fim_dado.bind("<Key>", lambda event: handle_keypress_nohour(event, fim_dado))

    salvar = tk.Entry(parent, width=20)
    salvar.grid(row=4, column=1, padx=5, pady=5, sticky="w")
    salvar.bind("<Key>", lambda event: handle_nokeypress(event))

    procura_diret = tk.Button(parent, text="Procurar", command=lambda: browser(salvar))
    procura_diret.grid(row=4, column=2, padx=5, pady=5)

    botao_start = tk.Button(parent, text="Começar", command=lambda: iniciar(local, inicio_dado, fim_dado, salvar))
    botao_start.grid(row=5, columnspan=3, padx=5, pady=5)


def iniciar(local, inicio_dado, fim_dado, salvar):
    cidade = local.get()
    dia_inicio = inicio_dado.get()
    dia_fim = fim_dado.get()
    caminho_arquivo = salvar.get()

    data_inicio_dt = datetime.strptime(dia_inicio, "%d/%m/%Y")
    data_fim_dt = datetime.strptime(dia_fim, "%d/%m/%Y")

    numero_dias = (data_fim_dt - data_inicio_dt).days+1
    if not cidade or not dia_inicio or not dia_fim:
        messagebox.showwarning("Atenção", "Por favor, insira todos os dados")
        return
    executar_processamento(cidade, int(numero_dias), caminho_arquivo, data_inicio_dt)


def main():
    carregar_api_key()
    root = tk.Tk()
    root.title("Previsão do Tempo")
    root.iconbitmap('stitch_ico.ico')
    criar_menu(root)
    criar_tela_principal_com_abas(root)
    root.mainloop()


if __name__ == "__main__":
    main()