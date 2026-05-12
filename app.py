import streamlit as st
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Caixa de Obra | M e Lopes", layout="wide")

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

# 3. TABELA DE LANÇAMENTOS (O "Excel" embutido)
st.write("### 3. Lançamento de Recibos e Notas")

# Criando a estrutura das colunas igual ao seu Excel
if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(
        columns=["Data", "Objeto", "Valor (R$)", "Centro de Custos"]
    )

# Editor de tabela dinâmico
despesas_editadas = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic", # Permite adicionar linhas infinitas
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f", min_value=0.0),
        "Centro de Custos": st.column_config.SelectboxColumn(
            options=["Vale alimentação", "Combustível", "Canteiro de obras", "Material Elétrico", "Despesas com viagem"]
        )
    }
)

# 4. PROCESSAMENTO E AUDITORIA (Lógica Financeira)
st.write("### 4. Resumo Financeiro")
total_gasto = despesas_editadas["Valor (R$)"].sum()
saldo = total_gasto - adiantamento

colA, colB, colC = st.columns(3)
colA.metric("Total Gasto na Obra", f"R$ {total_gasto:,.2f}")
colB.metric("Adiantamento", f"R$ {adiantamento:,.2f}")

if saldo > 0:
    colC.metric("A Reembolsar (Pagar ao Func.)", f"R$ {saldo:,.2f}", delta="Saída de Caixa", delta_color="inverse")
elif saldo < 0:
    colC.metric("Saldo em Caixa (Devolver)", f"R$ {abs(saldo):,.2f}", delta="Retorno para a Empresa", delta_color="normal")
else:
    colC.metric("Situação do Caixa", "R$ 0,00", delta="Caixa Zerado")
st.info("Na próxima etapa técnica, o botão abaixo irá gerar o PDF com a sua logomarca formatada.")
if st.button("Gerar PDF de Conferência"):
    st.success("Tabela processada com sucesso no backend!")
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Caixa de Obra | M e Lopes", layout="wide")

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

# 4. PROCESSAMENTO FINANCEIRO
st.write("### 4. Resumo Financeiro")
total_gasto = despesas_editadas["Valor (R$)"].sum()
saldo = total_gasto - adiantamento

colA, colB, colC = st.columns(3)
colA.metric("Total Gasto na Obra", f"R$ {total_gasto:,.2f}")
colB.metric("Adiantamento", f"R$ {adiantamento:,.2f}")

status_caixa = "Caixa Zerado"
if saldo > 0:
    status_caixa = f"A Reembolsar (Pagar ao Func.) - R$ {saldo:,.2f}"
    colC.metric("A Reembolsar", f"R$ {saldo:,.2f}", delta="Saída", delta_color="inverse")
elif saldo < 0:
    status_caixa = f"Saldo em Caixa (Devolver) - R$ {abs(saldo):,.2f}"
    colC.metric("Saldo em Caixa", f"R$ {abs(saldo):,.2f}", delta="Retorno", delta_color="normal")
else:
    colC.metric("Situação", "R$ 0,00")

# 5. MOTOR DE EXPORTAÇÃO (NOVIDADE)
st.write("---")
st.write("### 5. Exportação Oficial")

# Função para converter a tabela do ecrã para código HTML
tabela_html = despesas_editadas.to_html(index=False, border=1, justify="center")

# O Template Visual do Relatório
relatorio_html = f"""
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; margin: 40px; }}
        .header {{ border-bottom: 3px solid #0f172a; padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; }}
        h1 {{ color: #0f172a; font-size: 18pt; margin: 0; text-transform: uppercase; }}
        .subtitle {{ font-size: 10pt; color: #64748b; font-weight: bold; }}
        .caixa-dados {{ background-color: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10pt; }}
        th {{ background-color: #0f172a; color: white; padding: 10px; text-align: left; }}
        td {{ border-bottom: 1px solid #e2e8f0; padding: 8px; }}
        .resultado {{ font-size: 14pt; font-weight: bold; color: #b91c1c; margin-top: 20px; text-align: right; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Relatório de Caixa de Obra</h1>
            <div class="subtitle">G.A SOLAR | Processamento: M e Lopes Assessoria</div>
        </div>
        <div style="text-align: right; font-size: 9pt;">
            Data: {datetime.now().strftime("%d/%m/%Y")}
        </div>
    </div>

    <div class="caixa-dados">
        <p><strong>Responsável:</strong> {funcionario} &nbsp;|&nbsp; <strong>Banco:</strong> {banco} &nbsp;|&nbsp; <strong>PIX:</strong> {chave_pix}</p>
        <p><strong>Adiantamento Recebido:</strong> R$ {adiantamento:,.2f}</p>
    </div>

    <h3>Detalhamento de Despesas</h3>
    {tabela_html}

    <div class="resultado">
        Total Gasto: R$ {total_gasto:,.2f}<br>
        <span style="color: #0f172a; font-size: 12pt;">Resultado Final: {status_caixa}</span>
    </div>

    <p style="margin-top: 50px; font-size: 8pt; text-align: center; color: #94a3b8;">
        Documento gerado eletronicamente.
    </p>
</body>
</html>
"""

# Cria o botão de transferência
st.download_button(
    label="📄 Transferir Relatório para PDF",
    data=relatorio_html,
    file_name=f"Caixa_Obra_{funcionario.replace(' ', '_')}.html",
    mime="text/html"
)
