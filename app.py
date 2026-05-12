import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. SETUP
st.set_page_config(page_title="M e Lopes | Financeiro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [data-testid="stSidebar"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; border-left: 5px solid #38bdf8; }
    .main-header { font-size: 32px; font-weight: 800; color: #0f172a; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

# 2. ESTADO DA SESSÃO
if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])

if 'clientes' not in st.session_state:
    st.session_state.clientes = {"Wellington Rafael": "014.565.671-36", "G.A Solar (Geral)": "66.283.560/0001-09"}

# 3. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color: #0f172a;'>M e Lopes</h2>", unsafe_allow_html=True)
    st.caption("Versão 6.3 - Cálculo Blindado")
    st.divider()
    cliente_ativo = st.selectbox("Responsável", options=list(st.session_state.clientes.keys()))
    if st.button("🗑️ Limpar Tudo"):
        st.session_state.despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])
        st.rerun()

# 4. ENTRADA DE DADOS (PARSER)
st.markdown(f"<div class='main-header'>Gestão de Caixa: {cliente_ativo}</div>", unsafe_allow_html=True)

with st.expander("📥 Importar do Excel / Extração (Colar)", expanded=True):
    texto = st.text_area("Cole as colunas aqui:", height=100)
    if st.button("Processar Dados"):
        if texto:
            df_temp = pd.read_csv(io.StringIO(texto), sep='\t', names=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])
            
            # LIMPEZA DOS VALORES (Onde estava o erro)
            df_temp["Valor (R$)"] = df_temp["Valor (R$)"].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df_temp["Valor (R$)"] = pd.to_numeric(df_temp["Valor (R$)"], errors='coerce').fillna(0.0)
            
            st.session_state.despesas = pd.concat([st.session_state.despesas, df_temp], ignore_index=True)
            st.rerun()

# 5. TABELA DE CONFERÊNCIA
st.markdown("### 📝 Itens Lançados")
# Garantir que a coluna de valor é numérica antes de mostrar
st.session_state.despesas["Valor (R$)"] = pd.to_numeric(st.session_state.despesas["Valor (R$)"], errors='coerce').fillna(0.0)

despesas_finais = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
        "Centro de Custos": st.column_config.SelectboxColumn(options=["Alimentação", "Combustível", "Viagem", "Material", "Outros"])
    }
)

# 6. ANEXOS E CÁLCULOS
st.markdown("### 📎 Anexar Comprovantes")
arquivos = st.file_uploader("Upload de PDFs", accept_multiple_files=True)

st.divider()

# CÁLCULOS ROBUSTOS
total_gasto = float(despesas_finais["Valor (R$)"].sum())
adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, value=0.0, step=100.0)
saldo_final = total_gasto - adiantamento
status = "REEMBOLSO (Receber)" if saldo_final > 0 else "DEVOLUÇÃO (Sobra)"

col1, col2, col3 = st.columns(3)
col1.metric("TOTAL GASTO", f"R$ {total_gasto:,.2f}")
col2.metric("ADIANTAMENTO", f"R$ {adiantamento:,.2f}")
col3.metric(status, f"R$ {abs(saldo_final):,.2f}", delta="- Saída" if saldo_final > 0 else "+ Sobra")

# 7. RELATÓRIO
if not despesas_finais.empty:
    tabela_html = despesas_finais.to_html(index=False, border=0)
    anexos_txt = "".join([f"<li>{a.name}</li>" for a in arquivos]) if arquivos else "Nenhum"
    
    relatorio = f"""
    <html>
    <body style='font-family: sans-serif; padding: 20px;'>
        <h1>M e Lopes | Fechamento</h1>
        <p><b>Responsável:</b> {cliente_ativo} | <b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
        <div style='background: #f0f9ff; padding: 15px; border-radius: 10px;'>
            <b>Gasto:</b> R$ {total_gasto:,.2f} | <b>Adiantamento:</b> R$ {adiantamento:,.2f} | <b>{status}:</b> R$ {abs(saldo_final):,.2f}
        </div>
        <br>{tabela_html}
        <p><b>Comprovantes:</b> {anexos_txt}</p>
    </body>
    </html>
    """
    
    st.download_button("🚀 Gerar PDF/Relatório", data=relatorio, file_name=f"Relatorio_{cliente_ativo}.html", mime="text/html")
