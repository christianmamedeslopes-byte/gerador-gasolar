import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="M e Lopes | Cloud Finance", layout="wide")

# 2. DESIGN DA INTERFACE (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"] { font-family: 'Inter', sans-serif; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #0f172a; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #1e293b; color: #3b82f6; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; color: #0f172a; }
    .card { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_stdio=True)

# 3. GESTÃO DE CLIENTES
if 'clientes' not in st.session_state:
    st.session_state.clientes = {
        "Wellington Rafael": {"pix": "014.565.671-36", "banco": "Santander"},
        "G.A Solar (Geral)": {"pix": "66.283.560/0001-09", "banco": "PJ Bank"}
    }

# 4. SIDEBAR
with st.sidebar:
    st.markdown("<h1 style='color: #0f172a; margin-bottom: 0;'>M e Lopes</h1>", unsafe_allow_stdio=True)
    st.caption("Assessoria em Tecnologia")
    st.divider()
    cliente_selecionado = st.selectbox("🎯 Obra/Cliente Ativo", options=list(st.session_state.clientes.keys()))
    
    with st.expander("➕ Novo Cadastro"):
        n_nome = st.text_input("Nome")
        n_pix = st.text_input("PIX")
        n_banco = st.text_input("Banco")
        if st.button("Salvar Cliente"):
            if n_nome:
                st.session_state.clientes[n_nome] = {"pix": n_pix, "banco": n_banco}
                st.rerun()

# 5. CORPO PRINCIPAL
st.title("Caixa de Obra")
st.markdown(f"**Favorecido:** {cliente_selecionado} | **PIX:** {st.session_state.clientes[cliente_selecionado]['pix']}")

col_cfg, col_info = st.columns([1, 2])
with col_cfg:
    adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, step=100.0)

# TABELA DE LANÇAMENTOS
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

arquivos = st.file_uploader("📎 Anexar Comprovantes", accept_multiple_files=True)

# CÁLCULOS FINANCEIROS
total = despesas_editadas["Valor (R$)"].sum()
saldo = total - adiantamento
status = "REEMBOLSO" if saldo > 0 else "DEVOLUÇÃO"

st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Gasto Total", f"R$ {total:,.2f}")
m2.metric("Saldo Inicial", f"R$ {adiantamento:,.2f}")
m3.metric(status, f"R$ {abs(saldo):,.2f}", delta="- Fluxo" if saldo > 0 else "+ Caixa", delta_color="inverse" if saldo > 0 else "normal")

# 6. RELATÓRIO MODERNO (HTML)
tabela_html = despesas_editadas.to_html(index=False, border=0)
lista_anexos = "".join([f"<li>{a.name}</li>" for a in arquivos]) if arquivos else "Nenhum"

relatorio_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; color: #1e293b; padding: 40px; line-height: 1.5; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; }}
        .summary-grid {{ display: flex; gap: 20px; margin: 30px 0; }}
        .card {{ background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; flex: 1; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ text-align: left; padding: 12px; font-size: 8pt; color: #64748b; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; }}
        td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 10pt; }}
        .footer {{ margin-top: 50px; text-align: center; color: #94a3b8; font-size: 9pt; border-top: 1px solid #f1f5f9; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 20pt; font-weight: 800; color: #0f172a;">M e Lopes</div>
        <div style="text-align: right; color: #64748b;">Emitido em: {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>

    <h2 style="margin-top: 30px;">Caixa de Obra: {cliente_selecionado}</h2>

    <div class="summary-grid">
        <div class="card"><strong>TOTAL GASTO</strong><br>R$ {total:,.2f}</div>
        <div class="card"><strong>ADIANTAMENTO</strong><br>R$ {adiantamento:,.2f}</div>
        <div class="card" style="border-left: 4px solid #0f172a;"><strong>{status}</strong><br>R$ {abs(saldo):,.2f}</div>
    </div>

    {tabela_html}

    <div style="margin-top: 30px; font-size: 9pt;">
        <strong>COMPROVANTES:</strong>
        <ul>{lista_anexos}</ul>
    </div>

    <div class="footer">
        <strong>M e Lopes, assessoria em tecnologia</strong><br>
        Documento digital gerado para G.A Solar
    </div>
</body>
</html>
"""

st.download_button("🚀 Gerar Relatório Premium", data=relatorio_html, file_name=f"Relatorio_{cliente_selecionado}.html", mime="text/html")
st.markdown("<br><p style='text-align:center; color:#94a3b8; font-size:10px;'>M e Lopes, assessoria em tecnologia</p>", unsafe_allow_stdio=True)
