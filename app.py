import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Caixa de Obra | M e Lopes", layout="wide")

# Cabeçalho do Sistema
st.title("Fechamento de Caixa e Reembolso")
st.subheader("G.A Solar - Engenharia Financeira")

# 1. DADOS DO FAVORECIDO
st.write("### 1. Dados para Reembolso")
col1, col2, col3 = st.columns(3)
funcionario = col1.text_input("Funcionário", value="Wellington Rafael")
chave_pix = col2.text_input("Chave PIX / CPF")
banco = col3.text_input("Banco")

# 2. CONTROLE DE CAIXA
st.write("### 2. Controle de Saldo Inicial")
adiantamento = st.number_input("Valor do Adiantamento Fornecido (R$)", min_value=0.0, step=100.0)

# 3. TABELA DE LANÇAMENTOS
st.write("### 3. Lançamento de Recibos e Notas")

if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(
        columns=["Data", "Objeto", "Valor (R$)", "Centro de Custos"]
    )

despesas_editadas = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f", min_value=0.0),
        "Centro de Custos": st.column_config.SelectboxColumn(
            options=["Vale alimentação", "Combustível", "Canteiro de obras", "Material Elétrico", "Despesas com viagem"]
        )
    }
)

# 3.1 ANEXOS (NOVIDADE)
st.write("### 3.1 Anexar Comprovantes (Digitalização)")
arquivos_anexados = st.file_uploader(
    "Arraste os recibos (PDF, PNG, JPG)", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

lista_anexos_html = ""
if arquivos_anexados:
    st.success(f"{len(arquivos_anexados)} comprovante(s) carregado(s).")
    lista_anexos_html = "<ul>" + "".join([f"<li>{arq.name}</li>" for arq in arquivos_anexados]) + "</ul>"

# 4. PROCESSAMENTO FINANCEIRO
st.write("### 4. Resumo Financeiro")
total_gasto = despesas_editadas["Valor (R$)"].sum()
saldo = total_gasto - adiantamento

colA, colB, colC = st.columns(3)
colA.metric("Total Gasto", f"R$ {total_gasto:,.2f}")
colB.metric("Adiantamento", f"R$ {adiantamento:,.2f}")

if saldo > 0:
    status_caixa = f"A REEMBOLSAR: R$ {saldo:,.2f}"
    colC.metric("A Reembolsar", f"R$ {saldo:,.2f}", delta="Saída", delta_color="inverse")
elif saldo < 0:
    status_caixa = f"SALDO EM CAIXA (DEVOLVER): R$ {abs(saldo):,.2f}"
    colC.metric("Saldo em Caixa", f"R$ {abs(saldo):,.2f}", delta="Retorno", delta_color="normal")
else:
    status_caixa = "CAIXA ZERADO"
    colC.metric("Situação", "R$ 0,00")

# 5. GERADOR DE RELATÓRIO
st.write("---")
tabela_html = despesas_editadas.to_html(index=False, border=1, justify="center")

relatorio_html = f"""
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: sans-serif; color: #333; margin: 30px; line-height: 1.5; }}
        .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 20px; }}
        .box {{ background-color: #f1f5f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #cbd5e1; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
        th {{ background-color: #0f172a; color: white; padding: 8px; }}
        td {{ border: 1px solid #e2e8f0; padding: 6px; text-align: center; }}
        .footer-total {{ text-align: right; font-weight: bold; font-size: 12pt; margin-top: 20px; color: #1e293b; }}
        .anexos {{ margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 10px; font-size: 9pt; }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">RELATÓRIO DE CAIXA DE OBRA - G.A SOLAR</h2>
        <small>Processado por: M e Lopes Assessoria | {datetime.now().strftime("%d/%m/%Y %H:%M")}</small>
    </div>

    <div class="box">
        <strong>Funcionário:</strong> {funcionario} <br>
        <strong>Dados PIX:</strong> {banco} - {chave_pix} <br>
        <strong>Adiantamento:</strong> R$ {adiantamento:,.2f}
    </div>

    {tabela_html}

    <div class="footer-total">
        TOTAL GASTO: R$ {total_gasto:,.2f} <br>
        STATUS FINAL: {status_caixa}
    </div>

    <div class="anexos">
        <strong>Checklist de Comprovantes Anexados:</strong>
        {lista_anexos_html if arquivos_anexados else "<p>Nenhum comprovante digital anexado.</p>"}
    </div>
</body>
</html>
"""

st.download_button(
    label="📄 Gerar e Transferir Relatório PDF",
    data=relatorio_html,
    file_name=f"Caixa_{funcionario}_{datetime.now().strftime('%d_%m')}.html",
    mime="text/html"
)
