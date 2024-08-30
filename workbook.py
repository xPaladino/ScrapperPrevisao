from openpyxl import load_workbook

def formatar_workbook(file_name):
    wb = load_workbook(file_name)
    ws = wb.active

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    wb.save(file_name)
    print(f'Arq \nuivo {file_name} salvo com sucesso!')