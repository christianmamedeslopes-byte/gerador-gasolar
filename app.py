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
