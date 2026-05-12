import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. CONFIGURAÇÃO PREMIUM
st.set_page_config(page_title="M e Lopes | Gestão Financeira", layout="wide")

# Customização CSS para visual Empresarial
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    /* Esconder elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Cards de Métricas Estilizados */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    /* Cabeçalho e Títulos */
    .company-title { font-size: 24px; font-weight: 700; color: #0f172a; margin-bottom: 5px; }
    .section-header { font-size: 18px; font-weight: 600; color: #334155; margin-top: 25px; margin-bottom: 15px; }
    
    /* Inputs e Botões */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        background-color: #0f172a !important;
        color: white !important;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTÃO DE ESTADO
if 'db_despesas' not in st.session_state:
    st.session_state.db_despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])

if 'lista_clientes' not in st.session_state:
    st.session_state.lista_clientes = {
        "Wellington Rafael": "014.565.671-36",
        "G.A Solar (Geral)": "66.283.560/0001-09"
    }

# 3. BARRA LATERAL NAVEGACIONAL
with st.sidebar:
    st.markdown("<div class='company-title'>M e Lopes</div>", unsafe_allow_html=True)
    st.caption("Assessoria em Tecnologia e Gestão")
    st.divider()
    
    responsavel = st.selectbox("Unidade de Negócio / Responsável", options=list(st.session_state.lista_clientes.keys()))
    
    with st.expander("Configurações de Cadastro"):
        novo_c = st.text_input("Novo Responsável")
        novo_p = st.text_input("PIX de Repasse")
        if st.button("Salvar Cadastro"):
            if novo_c:
                st.session_state.lista_clientes[novo_c] = novo_p
                st.rerun()
                
    if st.button("Limpar Sessão Atual"):
        st.session_state.db_despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
        st.rerun()

# 4. PAINEL PRINCIPAL
st.markdown(f"<div class='company-title'>Relatório de Fluxo: {responsavel}</div>", unsafe_allow_html=True)
st.caption(f"Chave para Repasse: {st.session_state.lista_clientes[responsavel]}")

# Importador Inteligente
with st.expander("📥 Importação de Dados Externos", expanded=False):
    raw_input = st.text_area("Cole os dados da planilha aqui (Data, Fornecedor, Objeto, Valor, Categoria):", height=120)
    if st.button("Processar e Integrar"):
        if raw_input:
            try:
                new_data = pd.read_csv(io.StringIO(raw_input), sep='\t', names=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
                # Conversão robusta de tipos
                new_data["Valor"] = new_data["Valor"].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                new_data["Valor"] = pd.to_numeric(new_data["Valor"], errors='coerce').fillna(0.0)
                
                st.session_state.db_despesas = pd.concat([st.session_state.db_despesas, new_data], ignore_index=True)
                st.rerun()
            except Exception as e:
                st.error("Falha na interpretação dos dados. Verifique a formatação das colunas.")

# 5. CONFERÊNCIA E ANEXOS
st.markdown("<div class='section-header'>Detalhamento de Lançamentos</div>", unsafe_allow_html=True)

# Garante que a coluna valor é float antes de exibir
st.session_state.db_despesas["Valor"] = pd.to_numeric(st.session_state.db_despesas["Valor"], errors='coerce').fillna(0.0)

grid_dados = st.data_editor(
    st.session_state.db_despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0),
        "Categoria": st.column_config.SelectboxColumn(options=["Combustível", "Alimentação", "Viagem", "Material", "Outros"])
    }
)

up_files = st.file_uploader("Upload de Comprovantes Fiscais (PDF/Imagens)", accept_multiple_files=True)

# 6. DASHBOARD FINANCEIRO INTEGRADO
st.divider()
st.markdown("<div class='section-header'>Consolidação Financeira</div>", unsafe_allow_html=True)

# Cálculos com conversão garantida
val_gasto = float(grid_dados["Valor"].sum())

col_inp, col_gap = st.columns([1, 2])
with col_inp:
    val_adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, step=50.0, format="%.2f")

val_saldo = val_gasto - val_adiantamento
label_saldo = "REEMBOLSO DEVIDO" if val_saldo > 0 else "SALDO PARA DEVOLUÇÃO"

m1, m2, m3 = st.columns(3)
m1.metric("GASTO TOTAL", f"R$ {val_gasto:,.2f}")
m2.metric("ADIANTAMENTO", f"R$ {val_adiantamento:,.2f}")
m3.metric(label_saldo, f"R$ {abs(val_saldo):,.2f}", 
          delta="- Saída de Caixa" if val_saldo > 0 else "+ Sobra em Conta",
          delta_color="normal" if val_saldo <= 0 else "inverse")

# 7. EXPORTAÇÃO EXECUTIVA
if not grid_dados.empty:
    html_table = grid_dados.to_html(index=False, border=0, classes='table')
    lista_comprovantes = ", ".join([f.name for f in up_files]) if up_files else "Nenhum arquivo anexado."
    
    html_doc = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', sans-serif; padding: 40px; color: #1e293b; line-height: 1.5; }}
            .brand {{ font-size: 20pt; font-weight: 700; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }}
            .summary {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e2e8f0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ text-align: left; background: #f8fafc; padding: 12px; font-size: 9pt; color: #64748b; text-transform: uppercase; }}
            td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 10pt; }}
            .footer {{ margin-top: 50px; font-size: 8pt; color: #94a3b8; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="brand">M e Lopes | Intelligence</div>
        <p><b>Responsável:</b> {responsavel} | <b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
        <div class="summary">
            <b>Resumo Executivo:</b><br>
            Custos Totais: R$ {val_gasto:,.2f} | Adiantamentos: R$ {val_adiantamento:,.2f} | <b>{label_saldo}: R$ {abs(val_saldo):,.2f}</b>
        </div>
        {html_table}
        <p style="font-size: 9pt;"><b>Comprovantes Digitais:</b> {lista_comprovantes}</p>
        <div class="footer">Este documento é um relatório gerencial de uso interno da M e Lopes para G.A Solar.</div>
    </body>
    </html>
    """
    
    st.download_button("📂 Gerar Relatório Executivo (HTML)", data=html_doc, file_name=f"FIN_{responsavel}.html", mime="text/html")

st.markdown("<br><p style='text-align:center; color:#cbd5e1; font-size:10px;'>M e Lopes Business Solutions</p>", unsafe_allow_html=True)
