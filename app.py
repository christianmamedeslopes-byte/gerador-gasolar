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
# Garante que a base interna seja matemática antes de ir para a tela
st.session_state.db_despesas["Valor"] = pd.to_numeric(st.session_state.db_despesas["Valor"], errors='coerce').fillna(0.0)

grid_dados = st.data_editor(
    st.session_state.db_despesas, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", min_value=0.0),
        "Categoria": st.column_config.SelectboxColumn("Categoria", options=["Combustível", "Alimentação", "Viagem", "Material", "Outros"])
    }
)

# Soma blindada: força a conversão matemática da tabela final, ignorando textos
val_gasto = float(pd.to_numeric(grid_dados["Valor"], errors='coerce').fillna(0.0).sum()) if not grid_dados.empty else 0.0

val_adiantamento = st.number_input("Adiantamento Recebido (R$)", min_value=0.0, step=100.0)
val_saldo = val_gasto - val_adiantamento
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

# 3. Geração do Relatório PDF Corrigido e Modernizado
if not grid_dados.empty:
    logo_b64 = converter_imagem_base64("logo.png") 
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" height="45">' if logo_b64 else "<h2 style='color: #0f172a; margin: 0;'>M e Lopes</h2>"

    # CSS Padrão Executivo / Fintech
    css_pdf = """
        <style>
            @page {
                size: a4 portrait;
                margin: 2cm 2cm 2.5cm 2cm;
                @frame footer_frame {
                    -pdf-frame-content: footer_content;
                    left: 50pt; width: 512pt; top: 790pt; height: 20pt;
                }
            }
            body { font-family: Helvetica, sans-serif; color: #334155; }
            .header-table { width: 100%; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
            .title { font-size: 20px; font-weight: bold; color: #0f172a; text-align: right; margin: 0; }
            .subtitle { font-size: 10px; color: #64748b; text-align: right; margin: 0; }
            
            .kpi-table { width: 100%; background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; margin-bottom: 25px; }
            .kpi-label { font-size: 9px; color: #64748b; text-transform: uppercase; }
            .kpi-value { font-size: 14px; font-weight: bold; color: #0f172a; }
            .kpi-highlight { font-size: 14px; font-weight: bold; color: #0369a1; }
            
            .data-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .data-table th { background-color: #0f172a; color: #ffffff; padding: 10px 8px; font-size: 10px; text-transform: uppercase; text-align: left; }
            .data-table th.right { text-align: right; }
            .data-table td { border-bottom: 1px solid #e2e8f0; padding: 8px; font-size: 10px; }
            .data-table td.right { text-align: right; font-weight: bold; }
            .zebra { background-color: #f1f5f9; }
            
            #footer_content { text-align: center; font-size: 9px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 10px; }
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
                <td class="right">R$ {formatar_br(row['Valor'])}</td>
            </tr>
        """

    html_final = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            {css_pdf}
        </head>
        <body>
            <div id="footer_content">
                Desenvolvido por M e Lopes Assessoria em Tecnologia
            </div>

            <table class="header-table">
                <tr>
                    <td style="width: 50%; vertical-align: middle;">{logo_html}</td>
                    <td style="width: 50%; vertical-align: middle;">
                        <div class="title">Despesas com caixa de obra</div>
                        <div class="subtitle">Emissão: {datetime.now().strftime('%d/%m/%Y &agrave;s %H:%M')}</div>
                    </td>
                </tr>
            </table>

            <table class="kpi-table">
                <tr>
                    <td style="width: 33%;">
                        <div class="kpi-label">Responsável Ativo</div>
                        <div class="kpi-value">{responsavel}</div>
                    </td>
                    <td style="width: 33%;">
                        <div class="kpi-label">Gasto Total Acumulado</div>
                        <div class="kpi-value">R$ {formatar_br(val_gasto)}</div>
                    </td>
                    <td style="width: 34%;">
                        <div class="kpi-label">Adiantamento e Saldo</div>
                        <div style="font-size: 10px; color: #475569;">Provisão: R$ {formatar_br(val_adiantamento)}</div>
                        <div class="kpi-highlight">{'A Reembolsar' if val_saldo > 0 else 'Devolução'}: R$ {formatar_br(abs(val_saldo))}</div>
                    </td>
                </tr>
            </table>

            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 12%;">Data</th>
                        <th style="width: 30%;">Fornecedor</th>
                        <th style="width: 25%;">Objeto</th>
                        <th style="width: 18%;">Categoria</th>
                        <th class="right" style="width: 15%;">Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </body>
    </html>
    """

    pdf_bytes = gerar_pdf_profissional(html_final)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if pdf_bytes:
        st.download_button("📥 Baixar Relatório Executivo (PDF)", data=pdf_bytes, file_name=f"Relatorio_Caixa_{responsavel}.pdf", mime="application/pdf", use_container_width=True)
