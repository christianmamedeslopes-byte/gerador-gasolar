import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração com tema amplo
st.set_page_config(page_title="M e Lopes | Cloud Finance", layout="wide")

# --- CSS CUSTOMIZADO PARA A INTERFACE STREAMLIT ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #0f172a; color: white; border: none; }
    .stButton>button:hover { background-color: #1e293b; color: #3b82f6; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #0f172a; }
    </style>
    """, unsafe_allow_stdio=True)

# --- GESTÃO DE ESTADO E CLIENTES ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = {
        "Wellington Rafael": {"pix": "014.565.671-36", "banco": "Santander"},
        "G.A Solar (Geral)": {"pix": "66.283.560/0001-09", "banco": "PJ Bank"}
    }

# --- SIDEBAR MODERNA ---
with st.sidebar:
    st.markdown(f"<h1 style='color: #0f172a;'>M e Lopes</h1>", unsafe_allow_stdio=True)
    st.caption("Assessoria em Tecnologia")
    st.divider()
    
    cliente_selecionado = st.selectbox("🎯 Obra/Cliente Ativo", options=list(st.session_state.clientes.keys()))
    
    with st.expander("➕ Novo Cadastro"):
        n_nome = st.text_input("Nome")
        n_pix = st.text_input("PIX")
        n_banco = st.text_input("Banco")
        if st.button("Salvar"):
            if n_nome:
                st.session_state.clientes[n_nome] = {"pix": n_pix, "banco": n_banco}
                st.rerun()

# --- ÁREA PRINCIPAL ---
col_tit, col_dat = st.columns([3, 1])
col_tit.title("Caixa de Obra")
col_dat.markdown(f"<br><p style='text-align:right; color: #64748b;'>{datetime.now().strftime('%d/%m/%Y')}</p>", unsafe_allow_stdio=True)

with st.container():
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("### 💳 Financeiro")
        adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, step=100.0)
    with c2:
        st.markdown("### 📄 Identificação")
        st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0;">
                <strong>Favorecido:</strong> {cliente_selecionado}<br>
                <strong>Instituição:</strong> {st.session_state.clientes[cliente_selecionado]['banco']} | <strong>PIX:</strong> {st.session_state.clientes[cliente_selecionado]['pix']}
            </div>
        """, unsafe_allow_stdio=True)

st.divider()

# TABELA
st.markdown("### 📊 Lançamentos")
if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(columns=["Data", "Objeto", "Valor (R$)", "Centro de Custos"])

despesas_editadas = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Centro de Custos": st.column_config.SelectboxColumn(options=["Alimentação", "Combustível", "Material", "Viagem", "Outros"])
    }
)

# ANEXOS
arquivos = st.file_uploader("📎 Digitalizar Comprovantes", accept_multiple_files=True)

# CALCULOS
total = despesas_editadas["Valor (R$)"].sum()
saldo = total - adiantamento
status = "REEMBOLSO" if saldo > 0 else "DEVOLUÇÃO"

# DASHBOARD RESUMO
st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Gasto Total", f"R$ {total:,.2f}")
m2.metric("Saldo Inicial", f"R$ {adiantamento:,.2f}")
m3.metric(status, f"R$ {abs(saldo):,.2f}", delta="- Fluxo" if saldo > 0 else "+ Caixa")

# --- RELATÓRIO PDF (HTML MODERNO) ---
tabela_html = despesas_editadas.to_html(index=False, border=0)
lista_anexos = "".join([f"<li>{a.name}</li>" for a in arquivos]) if arquivos else "Nenhum"

relatorio_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; color: #1e293b; margin: 0; padding: 40px; background-color: #fff; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; margin-bottom: 30px; }}
        .brand {{ color: #0f172a; font-weight: 800; font-size: 20pt; letter-spacing: -1px; }}
        .badge {{ background-color: #f1f5f9; padding: 5px 12px; border-radius: 15px; font-size: 9pt; font-weight: bold; color: #475569; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; }}
        .summary-card small {{ color: #64748b; text-transform: uppercase; font-size: 8pt; font-weight: bold; }}
        .summary-card div {{ font-size: 14pt; font-weight: bold; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background-color: #f8fafc; color: #64748b; text-align: left; padding: 12px; font-size: 9pt; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; }}
        td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 10pt; }}
        .footer {{ margin-top: 60px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 20px; font-size: 9pt; color: #94a3b8; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="brand">M e Lopes</div>
        <div class="badge">Relatório de Fechamento</div>
    </div>

    <div style="margin-bottom: 30px;">
        <h2 style="margin:0; letter-spacing: -0.5px;">Caixa de Obra: {cliente_selecionado}</h2>
        <p style="color: #64748b; font-size: 10pt;">Processado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    </div>

    <div class="summary-grid">
        <div class="summary-card">
            <small>Total de Despesas</small>
            <div>R$ {total:,.2f}</div>
        </div>
        <div class="summary-card">
            <small>Adiantamento</small>
            <div>R$ {adiantamento:,.2f}</div>
        </div>
        <div class="summary-card" style="border-left: 4px solid #0f172a;">
            <small>{status}</small>
            <div style="color: #0f172a;">R$ {abs(saldo):,.2f}</div>
        </div>
    </div>

    {tabela_html.replace('class="dataframe"', 'class="table"')}

    <div style="margin-top: 30px;">
        <p style="font-size: 9pt; font-weight: bold; color: #64748b;">COMPROVANTES ANEXADOS:</p>
        <ul style="font-size: 9pt; color: #475569;">{lista_anexos}</ul>
    </div>

    <div class="footer">
        <strong>M e Lopes, assessoria em tecnologia</strong><br>
        Este documento é uma prestação de contas digital gerada via Cloud M e Lopes.
    </div>
</body>
</html>
"""

st.download_button("🚀 Exportar Relatório Premium", data=relatorio_html, file_name=f"Relatorio_{cliente_selecionado}.html", mime="text/html")
st.markdown("<br><p style='text-align:center; color:#94a3b8; font-size:10px;'>M e Lopes, assessoria em tecnologia</p>", unsafe_allow_stdio=True)
