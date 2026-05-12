import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ==========================================
# 1. CONFIGURAÇÃO E MOTOR DE ESTILOS (VIEW)
# ==========================================
st.set_page_config(page_title="M e Lopes | ERP Financeiro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    /* Clean UI Customization */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: 600; }
    
    div[data-testid="stMetric"] {
        background-color: #ffffff; border: 1px solid #e2e8f0; 
        padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .header-title { font-size: 28px; font-weight: 700; color: #0f172a; margin-bottom: 0px; letter-spacing: -0.5px; }
    .sub-title { font-size: 14px; color: #64748b; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS EM MEMÓRIA (MODEL)
# ==========================================
if 'db_despesas' not in st.session_state:
    st.session_state.db_despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])

if 'clientes' not in st.session_state:
    st.session_state.clientes = {"Wellington Rafael": "014.565.671-36", "G.A Solar": "66.283.560/0001-09"}

# ==========================================
# 3. FUNÇÕES DE NEGÓCIO (CONTROLLER)
# ==========================================
def limpar_valor_monetario(valor):
    """Garante que qualquer lixo digitado ou colado vire um número perfeito."""
    try:
        val_str = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(val_str)
    except:
        return 0.0

def processar_lote_excel(texto_colado):
    """Motor de processamento de dados copiados do Excel."""
    try:
        df_novo
