import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
from io import BytesIO
from xhtml2pdf import pisa

# ==========================================
# 1. CONFIGURAÇÃO E ESTILOS DA UI (STREAMLIT)
# ==========================================
st.set_page_config(page_title="M e Lopes | ERP Financeiro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    div[data-testid="stMetric"] {
        background-color: #ffffff; border: 1px solid #e2e8f0; 
        padding: 20px; border-radius: 12px;
    }
    .header-title { font-size: 28px; font-weight: 700; color: #0f172a; margin-bottom: 0px; }
    .sub-title { font-size: 14px; color: #64748b; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MODEL & CONTROLLER
# ==========================================
if 'db_despesas' not in st.session_state:
    st.session_state.db_despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])

if 'clientes' not in st.session_state:
    st.session_state.clientes = {"Wellington Rafael": "014.565.671-36", "G.A Solar": "66.283.560/0001-09"}

def formatar_br(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def converter_imagem_base64(path):
    """Auxiliar para injetar a logo no PDF."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

def gerar_pdf_profissional(html_content):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    return result.getvalue() if not pdf.err else None

# ==========================================
# 3. SIDEBAR E INPUTS
# ==========================================
with st.sidebar:
    st.markdown("<div class='header-title'>M e Lopes</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ERP Financeiro v10.0</div>", unsafe_allow_html=True)
    st.divider()
    responsavel = st.selectbox("👤 Responsável Ativo", options=list(st.session_state.clientes.keys()))
    if st.button("🗑️ Purgar Sessão", use_container_width=True, type="primary"):
        st.session_state.db_despesas = pd.DataFrame(columns=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
        st.rerun()

# Painel de Lançamentos (Simplificado para o exemplo)
st.markdown(f"### Painel: {responsavel}")
raw_input = st.text_area("Importação Rápida (Cole do Excel):", height=100)
if st.button("Importar Dados"):
    if raw_input:
        df_novo = pd.read_csv(io.StringIO(raw_input), sep='\t', names=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
        # Limpeza rápida de valores
        df_novo["Valor"] = df_novo["Valor"].apply(lambda x: float(str(x).replace('R$', '').replace('.', '').replace(',', '.').strip()) if isinstance(x, str) else x)
        st.session_state.db_despesas = pd.concat([st.session_state.db_despesas, df_novo], ignore_index=True)
        st.rerun()

# ==========================================
# 4. EXIBIÇÃO E CÁLCULOS
# ==========================================
grid_dados = st.data_editor(st.session_state.db_despesas, num_rows="dynamic", use_container_width=True)
val_gasto = float(grid_dados["Valor"].sum()) if not grid_dados.empty else 0.0
val_adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, step=100.0)
val_saldo = val_gasto - val_adiantamento

k1, k2, k3 = st.columns(3)
k1.metric("GASTO TOTAL", f"R$ {formatar_br(val_gasto)}")
k2.metric("ADIANTAMENTO", f"R$ {formatar_br(val_adiantamento)}")
k3.metric("SALDO FINAL", f"R$ {formatar_br(abs(val_saldo))}")

# ==========================================
# 5. MOTOR DE RELATÓRIO E VISUALIZADOR OTIMIZADO
# ==========================================
st.divider()
st.markdown("### 📄 Geração de Relatório e Anexos")

# 1. Upload Rápido (Armazena em memória sem renderizar)
up_files = st.file_uploader("Anexar Comprovantes para Conferência", accept_multiple_files=True)

# 2. Visualizador Lazy Loading (Carregamento Preguiçoso)
if up_files:
    st.success(f"✅ {len(up_files)} arquivo(s) em memória.")
    arquivo_selecionado = st.selectbox("Selecione um comprovante para auditar na tela:", [f.name for f in up_files])
    
    for file in up_files:
        if file.name == arquivo_selecionado:
            if file.type == "application/pdf":
                base64_pdf = base64.b64encode(file.getvalue()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.image(file, use_column_width=True)

# 3. Geração do Relatório PDF Corrigido
if not grid_dados.empty:
    logo_b64 = converter_imagem_base64("logo.png") 
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="150">' if logo_b64 else "<h2>M e Lopes</h2>"

    css_pdf = """
        <style>
            @page { size: a4; margin: 2cm; }
            body { font-family: Helvetica, sans-serif; color: #333; line-height: 1.4; }
            .header { border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 20px; }
            .title { font-size: 22px; font-weight: bold; color: #0f172a; }
            .summary-box { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10px; }
            th { background-color: #0f172a; color: white; padding: 8px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #e2e8f0; }
            .zebra { background-color: #f1f5f9; }
            .footer { position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 9px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 5px; }
        </style>
    """

    rows_html = ""
    for i, row in grid_dados.iterrows():
        classe = 'class="zebra"' if i % 2 == 0 else ""
        rows_html += f"""
            <tr {classe}>
                <td>{row['Data']}</td>
                <td>{row['Fornecedor']}</td>
                <td>{row['Objeto']}</td>
                <td>{row['Categoria']}</td>
                <td>R$ {formatar_br(row['Valor'])}</td>
            </tr>
        """

    # Tag meta charset adicionada para forçar a renderização correta de acentos latinos
    html_final = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            {css_pdf}
        </head>
        <body>
            <div class="header">
                <table style="border: none;">
                    <tr>
                        <td style="border: none; width: 50%;">{logo_html}</td>
                        <td style="border: none; width: 50%; text-align: right;">
                            <span class="title">Despesas com caixa de obra</span><br>
                            <span style="font-size: 10px;">Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                        </td>
                    </tr>
                </table>
            </div>

            <div class="summary-box">
                <b>Responsável:</b> {responsavel}<br>
                <b>Total Acumulado:</b> R$ {formatar_br(val_gasto)}<br>
                <b>Adiantamento:</b> R$ {formatar_br(val_adiantamento)}<br>
                <b style="font-size: 14px;">Saldo a {"Reembolsar" if val_saldo > 0 else "Devolver"}: R$ {formatar_br(abs(val_saldo))}</b>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Fornecedor</th>
                        <th>Objeto</th>
                        <th>Categoria</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <div class="footer">
                Desenvolvido por M e Lopes Assessoria em Tecnologia
            </div>
        </body>
    </html>
    """

    pdf_bytes = gerar_pdf_profissional(html_final)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if pdf_bytes:
        st.download_button("📥 Baixar Relatório Profissional (PDF)", data=pdf_bytes, file_name=f"Relatorio_Caixa_{responsavel}.pdf", mime="application/pdf", use_container_width=True)
