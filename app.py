import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA COM TEMA DARK-TECH
st.set_page_config(page_title="M e Lopes | Cloud Control", layout="wide")

# 2. DESIGN DA INTERFACE (CSS TECH)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;800&display=swap');
    
    html, body, [data-testid="stSidebar"] { font-family: 'Inter', sans-serif; }
    
    /* Estilo Tech para Métricas */
    div[data-testid="stMetricValue"] { 
        font-family: 'JetBrains Mono', monospace; 
        color: #0ea5e9; 
        font-size: 28px; 
    }
    
    /* Botão Estilo Comando */
    .stButton>button { 
        border-radius: 4px; 
        background-color: #0f172a; 
        color: #38bdf8; 
        border: 1px solid #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #38bdf8; 
        color: #0f172a; 
        box-shadow: 0 0 15px #38bdf8;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. BASE DE CLIENTES
if 'clientes' not in st.session_state:
    st.session_state.clientes = {
        "Wellington Rafael": {"pix": "014.565.671-36", "banco": "Santander"},
        "G.A Solar (Geral)": {"pix": "66.283.560/0001-09", "banco": "PJ Bank"}
    }

# 4. SIDEBAR
with st.sidebar:
    st.markdown("<h1 style='color: #38bdf8; font-family: JetBrains Mono;'>M e Lopes</h1>", unsafe_allow_html=True)
    st.caption("SYSTEM v5.0 | TECH CORE")
    st.divider()
    cliente_selecionado = st.selectbox("SISTEMA/CLIENTE", options=list(st.session_state.clientes.keys()))
    
    with st.expander("CADASTRO"):
        n_nome = st.text_input("NOME")
        n_pix = st.text_input("PIX")
        if st.button("EXECUTAR"):
            if n_nome:
                st.session_state.clientes[n_nome] = {"pix": n_pix, "banco": "Bco Genérico"}
                st.rerun()

# 5. DASHBOARD PRINCIPAL
st.markdown(f"<h2 style='letter-spacing: -1px;'>Controle de Caixa: <span style='color:#38bdf8;'>{cliente_selecionado}</span></h2>", unsafe_allow_html=True)

with st.container():
    c1, c2 = st.columns([1, 2])
    with c1:
        adiantamento = st.number_input("Adiantamento (R$)", min_value=0.0, step=100.0)
    with c2:
        st.markdown(f"""
            <div style="background-color: #0f172a; padding: 20px; border-radius: 8px; border-left: 5px solid #38bdf8; color: white;">
                <small style="color: #38bdf8; font-family: JetBrains Mono;">TERMINAL DE DADOS</small><br>
                <strong>CHAVE PIX:</strong> {st.session_state.clientes[cliente_selecionado]['pix']}
            </div>
        """, unsafe_allow_html=True)

st.write("---")

# 6. TABELA DE LANÇAMENTOS (COM FORNECEDOR)
st.markdown("### 🛠 Lançamentos de Campo")
if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(
        columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"]
    )

despesas_editadas = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Data": st.column_config.DateColumn("Data"),
        "Fornecedor": st.column_config.TextColumn("Fornecedor", help="Nome da loja ou empresa"),
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Centro de Custos": st.column_config.SelectboxColumn(options=["Alimentação", "Combustível", "Ferramental", "Material Elétrico", "Viagem"])
    }
)

arquivos = st.file_uploader("UPLOAD COMPROVANTES", accept_multiple_files=True)

# 7. CÁLCULOS
total = despesas_editadas["Valor (R$)"].sum()
saldo = total - adiantamento
status_txt = "REEMBOLSO" if saldo > 0 else "DEVOLUÇÃO"

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL GASTO", f"R$ {total:,.2f}")
m2.metric("ADIANTAMENTO", f"R$ {adiantamento:,.2f}")
m3.metric(status_txt, f"R$ {abs(saldo):,.2f}")

# 8. RELATÓRIO HTML (TEMA TECH)
tabela_html = despesas_editadas.to_html(index=False, border=0)
lista_anexos = "".join([f"<li>{a.name}</li>" for a in arquivos]) if arquivos else "Nenhum"

relatorio_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Inter:wght@400;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; padding: 40px; color: #1e293b; background: #fff; }}
        .header {{ border-bottom: 4px solid #0f172a; padding-bottom: 10px; display: flex; justify-content: space-between; }}
        .tech-box {{ background: #0f172a; color: #38bdf8; padding: 20px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10pt; }}
        th {{ background: #f1f5f9; text-align: left; padding: 12px; color: #475569; text-transform: uppercase; font-size: 8pt; }}
        td {{ padding: 10px; border-bottom: 1px solid #f1f5f9; }}
        .footer {{ margin-top: 50px; text-align: center; font-size: 8pt; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 24pt; font-weight: 800;">M e Lopes</div>
        <div style="text-align: right;">{datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    
    <div class="tech-box">
        >> IDENTIFICAÇÃO: {cliente_selecionado.upper()}<br>
        >> STATUS FINANCEIRO: {status_txt}<br>
        >> VALOR FINAL: R$ {abs(saldo):,.2f}
    </div>

    {tabela_html}

    <div style="margin-top: 30px; font-size: 9pt;">
        <strong>SISTEMA DE ANEXOS:</strong>
        <ul>{lista_anexos}</ul>
    </div>

    <div class="footer">
        M e Lopes, assessoria em tecnologia | Cloud Report v5.0
    </div>
</body>
</html>
"""

st.download_button("⚡️ EXPORTAR RELATÓRIO TECH", data=relatorio_html, file_name=f"Report_{cliente_selecionado}.html", mime="text/html")
st.markdown("<p style='text-align:center; color:#94a3b8; font-size:10px;'>M e Lopes, assessoria em tecnologia</p>", unsafe_allow_html=True)
