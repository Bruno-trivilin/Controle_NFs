import flet as ft
import sqlite3
import pandas as pd
import os

# Configuração do banco de dados
def setup_db():
    conn = sqlite3.connect("notas.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            nota_fiscal TEXT,
            data_emissao TEXT NOT NULL,
            data_vencimento TEXT NOT NULL,
            pago INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Função para atualizar o banco de dados caso a coluna "pago" ainda não exista
def atualizar_banco():
    conn = sqlite3.connect("notas.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE notas ADD COLUMN pago INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # A coluna já existe
    conn.close()

# Função para inserir nota
def inserir_nota(descricao, valor, nota_fiscal, data_emissao, data_vencimento):
    conn = sqlite3.connect("notas.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notas (descricao, valor, nota_fiscal, data_emissao, data_vencimento, pago) VALUES (?, ?, ?, ?, ?, 0)", 
                   (descricao, valor, nota_fiscal, data_emissao, data_vencimento))
    conn.commit()
    conn.close()

# Função para listar notas
def listar_notas():
    conn = sqlite3.connect("notas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notas")
    notas = cursor.fetchall()
    conn.close()
    return notas

# Função para marcar nota como paga
def marcar_como_paga(id_nota):
    conn = sqlite3.connect("notas.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE notas SET pago = 1 WHERE id = ?", (id_nota,))
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "Controle de Notas e Pagamentos"
    page.scroll = "adaptive"
    
    descricao_input = ft.TextField(label="Descrição")
    valor_input = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    nota_fiscal_input = ft.TextField(label="Número da Nota Fiscal")
    data_emissao_input = ft.TextField(label="Data Emissão Nota Fiscal", read_only=True)
    data_vencimento_input = ft.TextField(label="Data Vencimento Nota Fiscal", read_only=True)
    
    data_emissao_picker = ft.DatePicker(
        on_change=lambda e: selecionar_data_emissao(e, data_emissao_input))
    page.overlay.append(data_emissao_picker)

    data_vencimento_picker = ft.DatePicker(
        on_change=lambda e: selecionar_data_vencimento(e, data_vencimento_input))
    page.overlay.append(data_vencimento_picker)

    def selecionar_data_emissao(e, campo_data):
        if data_emissao_picker.value:
            campo_data.value = data_emissao_picker.value.strftime("%d/%m/%Y")
            page.update()

    botao_selecionar_data_emissao = ft.ElevatedButton(
        "Selecionar Data",
        icon="CALENDAR_MONTH",
        on_click=lambda e: data_emissao_picker.pick_date()
    )

    def selecionar_data_vencimento(e, campo_data):
        if data_vencimento_picker.value:
            campo_data.value = data_vencimento_picker.value.strftime("%d/%m/%Y")
            page.update()

    botao_selecionar_data_vencimento = ft.ElevatedButton(
        "Selecionar Data",
        icon="CALENDAR_MONTH",
        on_click=lambda e: data_vencimento_picker.pick_date()
    )

    def abrir_popup(e):
        popup.open = True
        page.update()
    
    def fechar_popup(e):
        popup.open = False
        page.update()
    
    def adicionar_nota(e):
        inserir_nota(descricao_input.value, float(valor_input.value), nota_fiscal_input.value, data_emissao_input.value, data_vencimento_input.value)
        descricao_input.value = ""
        valor_input.value = ""
        nota_fiscal_input.value = ""
        data_emissao_input.value = ""
        data_vencimento_input.value = ""
        atualizar_lista()
        fechar_popup(e)

    def exportar_para_excel(e):
        caminho_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        caminho_arquivo = os.path.join(caminho_downloads, "despesas.xlsx")

        conn = sqlite3.connect("notas.db")
        df = pd.read_sql_query("SELECT * FROM notas", conn)
        conn.close()

        df["pago"] = df["pago"].map({0: "Pendente", 1: "Pago"})

        df.to_excel(caminho_arquivo, index=False, engine="openpyxl")

        page.snack_bar = ft.SnackBar(ft.Text(f"Arquivo salvo em: {caminho_arquivo}"))
        page.snack_bar.open = True
        page.update()

    botao_exportar_excel = ft.ElevatedButton(
        "Exportar para Excel",
        icon="FILE_DOWNLOAD",
        on_click=exportar_para_excel
    )

    popup = ft.AlertDialog(
        modal=True,
        title=ft.Text("Adicionar Nova Despesa"),
        content=ft.Column([
            descricao_input,
            valor_input,
            nota_fiscal_input,
            data_emissao_input, 
            botao_selecionar_data_emissao,
            data_vencimento_input,
            botao_selecionar_data_vencimento,
        ], tight=True),
        actions=[
            ft.ElevatedButton("Adicionar Despesa", on_click=adicionar_nota),
            ft.TextButton("Cancelar", on_click=fechar_popup),
        ]
    )

    page.dialog = popup
    botao_abrir_popup = ft.ElevatedButton("+ Nova Despesa", on_click=abrir_popup)

    lista_notas = ft.Column()

    def atualizar_lista():
        lista_notas.controls.clear()
        for nota in listar_notas():
            id_nota, descricao, valor, nota_fiscal, data_emissao, data_vencimento, pago = nota

            cor_fundo = "red" if pago == 0 else "green"
            texto_botao = "Pagar" if pago == 0 else "Pago"
            icone_botao = "CHECK_CIRCLE" if pago == 1 else "PAYMENT"
            habilitar_botao = pago == 0

            botao_pagar = ft.ElevatedButton(
                texto_botao,
                icon=icone_botao,
                disabled=not habilitar_botao,
                on_click=lambda e, id_nota=id_nota: pagar_nota(id_nota)
            )

            lista_notas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{descricao}", size=18, weight="bold"),
                        ]),
                        ft.Row([
                            ft.Text(f"Valor: R${valor:.2f}  |  NF: {nota_fiscal}  |  Emissão: {data_emissao}  |  Vencimento: {data_vencimento}"),
                            botao_pagar
                        ], alignment="spaceBetween")
                    ]),
                    bgcolor=cor_fundo,
                    padding=10,
                    border_radius=5
                )
            )
        page.update()

    def pagar_nota(id_nota):
        marcar_como_paga(id_nota)
        atualizar_lista()

    page.add(
        ft.Column([
            botao_abrir_popup,
            botao_exportar_excel,
            lista_notas
        ])
    )

    atualizar_lista()

if __name__ == "__main__":
    setup_db()
    atualizar_banco()
    ft.app(target=main)
