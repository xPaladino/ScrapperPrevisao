import tkinter as tk
from tkinter import messagebox, filedialog
import processamento
from PIL import Image, ImageTk
from datetime import datetime
from unidecode import unidecode
import threading
import os
from workbook import formatar_workbook
import time

status_concluido = {"success": False}

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

    label.configure(image=frames[index])
    index = (index + 1) % len(frames)
    label.after(100, atualiza_gif, label, frames, index)

def tela_carregamento():
    carregamento = tk.Toplevel()
    carregamento.iconbitmap('tails_ico.ico')
    carregamento.title("Aguarde")
    carregamento.geometry("300x200")

    gif = Image.open("tails.gif")
    tamanho = (95,100)
    frames = redimensionar_gif(gif,tamanho)

    gif_label = tk.Label(carregamento)
    gif_label.pack()
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

def executar_processamento(cidade, dias, diretorio):
    def processar():
        cidade_formatada = formatar_cidade(cidade)
        base_url = f'https://www.accuweather.com/pt/br/{cidade_formatada}/40111/daily-weather-forecast/40111'
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/86.0.4240.198 Safari/537.36"
        }

        df = processamento.processar_dados(base_url, headers, dias,cidade)

        if not os.path.exists(diretorio):
            try:
                os.makedirs(diretorio)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível criar o diretório: {e}")
                status_concluido["success"] = False
                return

        file_name = os.path.join(diretorio, 'dados.xlsx')

        try:
            df.to_excel(file_name, index=False)
            formatar_workbook(file_name)
            status_concluido["success"] = True
            messagebox.showinfo("Sucesso", f"Dados salvos em {file_name}")

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo: {e}")

            status_concluido["success"] = False
        carregamento.destroy()

    carregamento = tela_carregamento()
    threading.Thread(target=processar).start()
def formatar_cidade(cidade):
    cidade_formatada = unidecode(cidade).replace(' ', '').lower()
    return cidade_formatada

def browser(entry):
    seleciona = filedialog.askdirectory()
    if seleciona:
        entry.delete(0, tk.END)
        entry.insert(tk.END, seleciona)
    else:
        messagebox.showwarning("Atenção","Por favor, selecione um diretório antes de continuar.")


def main():
    def iniciar():
        cidade = local.get()
        dia_inicio = inicio_dado.get()
        dia_fim = fim_dado.get()
        diretorio = salvar.get()

        data_inicio_dt = datetime.strptime(dia_inicio, "%d/%m/%Y")
        data_fim_dt = datetime.strptime(dia_fim, "%d/%m/%Y")

        numero_dias = (data_fim_dt - data_inicio_dt).days
        if not cidade or not dia_inicio or not dia_fim:
            messagebox.showwarning("Atenção", "Por favor, insira todos os dados")
            return
        executar_processamento(cidade, int(numero_dias),diretorio)

    root = tk.Tk()
    root.title("Previsão do Tempo")
    root.iconbitmap('tails_ico.ico')

    local_label = tk.Label(root, text="Cidade:")
    local_label.grid(row=1, column=0, padx=15, pady=5, sticky="w")

    data_inicio = tk.Label(root, text="Data Inicial:")
    data_inicio.grid(row=2, column=0, padx=15, pady=5, sticky="w")

    data_fim = tk.Label(root, text="Data Final:")
    data_fim.grid(row=3, column=0, padx=15, pady=5, sticky="w")

    salvar_label = tk.Label(root, text="Diretório")
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
        if event.char.isalpha() or event.keysym in ['BackSpace', 'Tab']:
            return True
        return "break"

    local = tk.Entry(root, width=12)
    local.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    local.bind("<Key>", lambda event: handle_keypress_nochar(event, local))

    inicio_dado = tk.Entry(root, width=12)
    inicio_dado.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    inicio_dado.bind("<Key>", lambda event: handle_keypress_nohour(event, inicio_dado))

    fim_dado = tk.Entry(root, width=12)
    fim_dado.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    fim_dado.bind("<Key>", lambda event: handle_keypress_nohour(event, fim_dado))

    salvar = tk.Entry(root, width=20)
    salvar.grid(row=4, column=1, padx=5, pady=5, sticky="w")
    salvar.bind("<Key>", lambda event: handle_nokeypress(event))

    procura_diret = tk.Button(root, text="Procurar", command=lambda: browser(salvar))
    procura_diret.grid(row=4, column=2, padx=5, pady=5)

    botao_start = tk.Button(root, text="Começar",
                            command=iniciar)
    botao_start.grid(row=5, columnspan=3, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
