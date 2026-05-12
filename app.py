import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. CONFIGURAÇÃO E TEMA
st.set_page_config(page_title="M e Lopes | Gestão de Caixa", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [data-testid="stSidebar"] { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 32px; font-weight: 800; color: #0f172a; letter-spacing: -1px; }
    .stMetric { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    .stTextArea textarea { border: 1px dashed #38bdf8; background-color: #f0f9ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DE MEMÓRIA (IMPORTANTE)
if 'clientes' not in st.session_state:
    st.session_state.clientes = {
        "Wellington Rafael": {"pix": "014.565.671-36"},
        "G.A Solar (Geral)": {"pix": "66.283.560/0001-09"}
    }

if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])

# 3. SIDEBAR: GESTÃO E CADASTRO
with st.sidebar:
    st.markdown("<h2 style='color: #0f172a;'>M e Lopes</h2>", unsafe_allow_html=True)
    st.caption("Controle de Fluxo v6.1")
    st.divider()
    
    cliente_ativo = st.selectbox("Responsável pela Obra", options=list(st.session_state.clientes.keys()))
    
    with st.expander("➕ Cadastrar Novo Cliente"):
        n_nome = st.text_input("Nome")
        n_pix = st.text_input("PIX")
        if st.button("Gravar Cliente"):
            if n_nome:
                st.session_state.clientes[n_nome] = {"pix": n_pix}
                st.rerun()

    if st.button("🗑️ Resetar Sistema"):
        st.session_state.despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])
        st.rerun()

# 4. ÁREA DE IMPORTAÇÃO (COPIAR E COLAR)
st.markdown(f"<div class='main-header'>Caixa: {cliente_ativo}</div>", unsafe_allow_html=True)
st.write(f"**Chave PIX:** {st.session_state.clientes[cliente_ativo]['pix']}")

with st.expander("📥 Importar Dados do Excel (Copiar/Colar)", expanded=True):
    st.info("Copie as 5 colunas do Excel (Data, Fornecedor, Objeto, Valor, Categoria) e cole abaixo.")
    texto_colado = st.text_area("Cole aqui os dados da sua planilha:", height=100)
    
    if st.button("Processar Colagem"):
        if texto_colado:
            try:
                df_temp = pd.read_csv(io.StringIO(texto_colado), sep='\t', names=["Data", "Fornecedor", "Objeto", "Valor (R$)", "Centro de Custos"])
                st.session_state.despesas = pd.concat([st.session_state.despesas, df_temp], ignore_index=True)
                st.success(f"{len(df_temp)} registros adicionados!")
                st.rerun()
            except:
                st.error("Erro no formato. Certifique-se de copiar exatamente 5 colunas.")

st.divider()

# 5. TABELA DE EDIÇÃO E CONFERÊNCIA
st.markdown("### 📝 Conferência de Lançamentos")
despesas_finais = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Centro de Custos": st.column_config.SelectboxColumn(options=["Alimentação", "Combustível", "Viagem", "Material", "Outros"])
    }
)

# 6. DASHBOARD E CÁLCULOS
total = despesas_finais["Valor (R$)"].sum()
adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, step=100.0)
saldo = total - adiantamento
status = "REEMBOLSO" if saldo > 0 else "DEVOLUÇÃO"

c1, c2, c3 = st.columns(3)
c1.metric("Total Gasto", f"R$ {total:,.2f}")
c2.metric("Adiantamento", f"R$ {adiantamento:,.2f}")
c3.metric(status, f"R$ {abs(saldo):,.2f}", delta="- Saída" if saldo > 0 else "+ Sobra")

# 7. GERADOR DE RELATÓRIO (DOWNLOAD)
tabela_html = despesas_finais.to_html(index=False, border=0)

relatorio_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; padding: 40px; color: #1e293b; }}
        .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; display: flex; justify-content: space-between; }}
        .card {{ background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #f8fafc; text-align: left; padding: 10px; font-size: 8pt; color: #64748b; text-transform: uppercase; }}
        td {{ padding: 10px; border-bottom: 1px solid #f1f5f9; font-size: 10pt; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 20pt; font-weight: 800;">M e Lopes</div>
        <div>{datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    <h2>Relatório de Caixa: {cliente_ativo}</h2>
    <div class="card">
        <strong>RESUMO FINANCEIRO:</strong><br>
        Gasto Total: R$ {total:,.2f} | Adiantamento: R$ {adiantamento:,.2f} | <strong>{status}: R$ {abs(saldo):,.2f}</strong>
    </div>
    {tabela_html}
    <p style="margin-top: 30px; font-size: 8pt; color: #94a3b8; text-align: center;">M e Lopes, assessoria em tecnologia</p>
</body>
</html>
"""

if not despesas_finais.empty:
    st.download_button(
        label="🚀 Baixar Relatório Premium",
        data=relatorio_html,
        file_name=f"Relatorio_{cliente_ativo}.html",
        mime="text/html"
    )
else:
    st.warning("Adicione lançamentos para habilitar o download.")

st.markdown("<p style='text-align:center; color:#94a3b8; font-size:10px;'>M e Lopes, assessoria em tecnologia</p>", unsafe_allow_html=True)
