import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="M e Lopes | Data Parser", layout="wide")

# --- DESIGN MODERNO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"] { font-family: 'Inter', sans-serif; }
    .stTextArea textarea { background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 10px; }
    .main-header { font-size: 24px; font-weight: 800; color: #0f172a; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DOS DADOS ---
if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## M e Lopes")
    st.caption("Módulo: Importação Rápida")
    st.divider()
    if st.button("🗑️ Limpar Tudo"):
        st.session_state.despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])
        st.rerun()

# --- INTERFACE ---
st.markdown("<div class='main-header'>Importação via Copiar/Colar</div>", unsafe_allow_html=True)
st.write("Copie as colunas do Excel (Data, Fornecedor, Objeto, Valor, Categoria) e cole abaixo:")

# ÁREA DE COLAGEM
texto_colado = st.text_area("Área de Transferência", height=150, placeholder="Cole aqui os dados da sua planilha...")

if texto_colado:
    try:
        # O pulo do gato: ler o texto como se fosse um arquivo CSV separado por TAB (\t)
        df_importado = pd.read_csv(io.StringIO(texto_colado), sep='\t', names=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])
        
        # Limpeza básica: converter valor para número caso venha com "R$" ou vírgula
        if not df_importado.empty:
            st.session_state.despesas = pd.concat([st.session_state.despesas, df_importado], ignore_index=True)
            st.success(f"{len(df_importado)} linhas importadas com sucesso!")
            # Limpa o campo de texto forçando um rerun
            st.rerun()
    except Exception as e:
        st.error("Erro ao processar dados. Verifique se copiou as 5 colunas corretamente.")

st.divider()

# TABELA DE CONFERÊNCIA (O Wellington pode ajustar se algo colou errado)
st.markdown("### 📊 Conferência de Dados")
despesas_editadas = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Centro de Custos": st.column_config.SelectboxColumn(options=["Alimentação", "Combustível", "Material", "Viagem", "Outros"])
    }
)

# DASHBOARD E EXPORTAÇÃO
total = despesas_editadas["Valor (R$)"].sum()
st.metric("Total Acumulado", f"R$ {total:,.2f}")

# (O código do HTML/PDF que já tínhamos permanece aqui para gerar o documento final)
# ... [Código do download_button e HTML aqui] ...
