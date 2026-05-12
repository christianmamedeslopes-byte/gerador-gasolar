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
        df_novo = pd.read_csv(io.StringIO(texto_colado), sep='\t', names=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
        df_novo["Valor"] = df_novo["Valor"].apply(limpar_valor_monetario)
        st.session_state.db_despesas = pd.concat([st.session_state.db_despesas, df_novo], ignore_index=True)
        return True, len(df_novo)
    except Exception as e:
        return False, 0

# ==========================================
# 4. INTERFACE DE USUÁRIO (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<div class='header-title'>M e Lopes</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ERP Financeiro v8.0</div>", unsafe_allow_html=True)
    st.divider()
    
    responsavel = st.selectbox("👤 Responsável Ativo", options=list(st.session_state.clientes.keys()))
    
    with st.expander("⚙️ Gestão de Cadastros"):
        n_nome = st.text_input("Novo Responsável")
        n_pix = st.text_input("Chave PIX")
        if st.button("Adicionar ao Sistema", use_container_width=True):
            if n_nome:
                st.session_state.clientes[n_nome] = n_pix
                st.rerun()
                
    st.divider()
    if st.button("🗑️ Purgar Dados da Sessão", use_container_width=True, type="primary"):
        st.session_state.db_despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
        st.rerun()

# ==========================================
# 5. PAINEL PRINCIPAL & ABAS DE TRABALHO
# ==========================================
st.markdown(f"<div class='header-title'>Painel de Auditoria: {responsavel}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>PIX Registrado: {st.session_state.clientes[responsavel]}</div>", unsafe_allow_html=True)

# Divisão de tarefas em Abas (UI Moderna)
aba_importacao, aba_manual = st.tabs(["📥 Importação em Lote (Excel)", "✍️ Lançamento Rápido"])

with aba_importacao:
    raw_input = st.text_area("Cole as 5 colunas do Excel/PDF extraído:", height=150, 
                             help="A ordem deve ser: Data | Fornecedor | Objeto | Valor | Categoria")
    if st.button("Executar Importação", type="secondary"):
        if raw_input:
            sucesso, qtd = processar_lote_excel(raw_input)
            if sucesso:
                st.success(f"✅ {qtd} registros importados com sucesso!")
                st.rerun()
            else:
                st.error("Falha no processamento. Verifique a estrutura dos dados.")

with aba_manual:
    st.markdown("Registre notas individuais rapidamente:")
    col_m1, col_m2, col_m3 = st.columns(3)
    m_data = col_m1.date_input("Data", format="DD/MM/YYYY")
    m_forn = col_m2.text_input("Fornecedor")
    m_obj = col_m3.text_input("Objeto (Ex: Gasolina)")
    
    col_m4, col_m5, col_m6 = st.columns(3)
    m_val = col_m4.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    m_cat = col_m5.selectbox("Categoria", ["Combustível", "Alimentação", "Viagem", "Material", "Outros"])
    
    if col_m6.button("➕ Inserir Linha", use_container_width=True):
        nova_linha = pd.DataFrame([{"Data": m_data.strftime("%d/%m/%Y"), "Fornecedor": m_forn, "Objeto": m_obj, "Valor": m_val, "Categoria": m_cat}])
        st.session_state.db_despesas = pd.concat([st.session_state.db_despesas, nova_linha], ignore_index=True)
        st.success("Lançamento efetuado.")
        st.rerun()

# ==========================================
# 6. MOTOR DE AUDITORIA (TABELA E GRÁFICOS)
# ==========================================
st.divider()
st.markdown("### 🔍 Detalhamento e Edição")

# Garante que os valores estão limpos para a exibição
st.session_state.db_despesas["Valor"] = st.session_state.db_despesas["Valor"].apply(limpar_valor_monetario)

grid_dados = st.data_editor(
    st.session_state.db_despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0),
        "Categoria": st.column_config.SelectboxColumn(options=["Combustível", "Alimentação", "Viagem", "Material", "Outros"])
    }
)

# Inteligência de Negócio (BI)
val_gasto = float(grid_dados["Valor"].sum())

col_kpi, col_chart = st.columns([2, 1])

with col_kpi:
    val_adiantamento = st.number_input("Adiantamento Recebido da G.A Solar (R$)", min_value=0.0, step=100.0)
    val_saldo = val_gasto - val_adiantamento
    label_saldo = "A REEMBOLSAR (Devido ao Func.)" if val_saldo > 0 else "DEVOLUÇÃO (Sobra em Caixa)"
    
    k1, k2, k3 = st.columns(3)
    k1.metric("GASTO TOTAL", f"R$ {val_gasto:,.2f}")
    k2.metric("ADIANTAMENTO", f"R$ {val_adiantamento:,.2f}")
    k3.metric(label_saldo, f"R$ {abs(val_saldo):,.2f}", 
              delta="- Saída" if val_saldo > 0 else "+ Caixa", 
              delta_color="normal" if val_saldo <= 0 else "inverse")

with col_chart:
    st.markdown("**Distribuição de Custos**")
    if not grid_dados.empty:
        # Cria um dashboard nativo baseado nas categorias
        resumo_cat = grid_dados.groupby("Categoria")["Valor"].sum().reset_index()
        st.dataframe(
            resumo_cat, 
            column_config={
                "Categoria": "Centro de Custos",
                "Valor": st.column_config.ProgressColumn("Volume Financeiro", format="R$ %.2f", min_value=0, max_value=float(val_gasto))
            }, 
            hide_index=True, use_container_width=True
        )
    else:
        st.caption("Aguardando lançamentos para gerar análise.")

# ==========================================
# 7. SISTEMA DE ANEXOS E EXPORTAÇÃO
# ==========================================
st.divider()
up_files = st.file_uploader("📎 Digitalizar Comprovantes (Anexos Legais)", accept_multiple_files=True)

col_exp1, col_exp2 = st.columns(2)

if not grid_dados.empty:
    html_table = grid_dados.to_html(index=False, border=0)
    lista_comprovantes = ", ".join([f.name for f in up_files]) if up_files else "Nenhum"
    
    # Gerador HTML Otimizado
    html_doc = f"""
    <html>
    <body style="font-family: 'Inter', sans-serif; padding: 40px; color: #1e293b;">
        <h2 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">M e Lopes | Fechamento de Obra</h2>
        <p><b>Responsável:</b> {responsavel} | <b>Emissão:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
        <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <b style="font-size: 16px;">Consolidação Financeira:</b><br><br>
            Custo Operacional Total: R$ {val_gasto:,.2f} <br>
            Adiantamento Disponibilizado: R$ {val_adiantamento:,.2f} <br>
            <b style="color: #0f172a; font-size: 18px;">Resultado Final ({label_saldo}): R$ {abs(val_saldo):,.2f}</b>
        </div>
        {html_table}
        <p style="margin-top: 20px; font-size: 12px; color: #64748b;"><b>Comprovantes Analisados:</b> {lista_comprovantes}</p>
    </body>
    </html>
    """
    
    with col_exp1:
        st.download_button("📄 Emitir Relatório Oficial (HTML/PDF)", data=html_doc, file_name=f"Relatorio_{responsavel}.html", mime="text/html", use_container_width=True)
    with col_exp2:
        csv_backup = grid_dados.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Backup de Dados (CSV)", data=csv_backup, file_name=f"Backup_{responsavel}.csv", mime="text/csv", use_container_width=True)
